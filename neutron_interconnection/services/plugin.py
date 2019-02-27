# Copyright (c) 2018 Orange.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy

from oslo_log import log as logging

from neutronclient.common import exceptions as neutronclient_exc

from neutron_lib.api.definitions import interconnection as inter_api_def
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib.db import api as db_api

from neutron.db import common_db_mixin
from neutron.db import db_base_plugin_common
from neutron.objects import base as objects_base

from neutron_interconnection.extensions import interconnection as inter_ext
from neutron_interconnection.objects import interconnection as inter_objs
from neutron_interconnection.services.common import callbacks \
    as inter_callbacks
from neutron_interconnection.services.common import constants as inter_consts
from neutron_interconnection.services.common import exceptions as inter_exc
from neutron_interconnection.services.common import utils as inter_utils
from neutron_interconnection.services.drivers import base as driver_base
from neutron_interconnection.services import lifecycle_fsm
from neutron_interconnection.services import state_scheduler_worker

LOG = logging.getLogger(__name__)


class NeutronInterconnectionPlugin(inter_ext.NeutronInterconnectionPluginBase,
                                   common_db_mixin.CommonDbMixin):

    supported_extension_aliases = [inter_api_def.ALIAS]
    path_prefix = inter_api_def.API_PREFIX

    def __init__(self):
        super(NeutronInterconnectionPlugin, self).__init__()
        self.drivers = driver_base.register_drivers()

        state_scheduler = (
            state_scheduler_worker.StateSchedulerWorker(self.drivers)
        )
        self.add_worker(state_scheduler)

    def _get_interconnection(self, context, interconnection_id):
        """Return interconnection object or raise if not found."""
        obj = inter_objs.Interconnection.get_object(context,
                                                    id=interconnection_id)
        if obj is None:
            raise inter_exc.InterconnectionNotFound(id=interconnection_id)

        return obj

    def _check_type_compatibility_with_symmetric(self, interconnection_obj):
        """Check interconnection type compatibility with symmetric one."""
        neutron_client = inter_utils.get_neutron_client(
            interconnection_obj.remote_keystone,
            interconnection_obj.remote_region
        )

        filters = {
            'local_resource_id': interconnection_obj.remote_resource_id,
            'remote_resource_id': interconnection_obj.local_resource_id
        }

        try:
            remote_interconnections = (
                neutron_client.list_interconnections(
                    **filters)['interconnections']
            )

            if remote_interconnections:
                remote_interconnection = remote_interconnections.pop()
                if interconnection_obj.type != remote_interconnection['type']:
                    raise inter_exc.IncompatibleInterconnectionType()
        except neutronclient_exc.ConnectionFailed:
            LOG.error("Interconnection type compatibility not verified: "
                      "Can't connect to remote neutron")
        except neutronclient_exc.Unauthorized:
            LOG.error("Connection refused to remote neutron")

    @db_base_plugin_common.convert_result_to_dict
    def create_interconnection(self, context, interconnection):
        """Create an interconnection."""
        interconnection_data = interconnection['interconnection']
        # interconnection data contains both tenant_id and project_id, so we
        # need to remove redundant keyword.
        interconnection_data.pop('tenant_id', None)
        interconnection_obj = inter_objs.Interconnection(
            context, **interconnection_data
        )

        self._check_type_compatibility_with_symmetric(interconnection_obj)

        with db_api.autonested_transaction(context.session):
            interconnection_obj.create()

            payload = inter_callbacks.InterconnectionPayload(
                context, interconnection_obj.id,
                current_interconnection=interconnection_obj)
            registry.notify(
                inter_consts.INTERCONNECTION, events.PRECOMMIT_CREATE, self,
                payload=payload)

        registry.notify(
            inter_consts.INTERCONNECTION, events.AFTER_CREATE, self,
            payload=payload)

        return interconnection_obj

    @db_base_plugin_common.convert_result_to_dict
    def update_interconnection(self, context, interconnection_id,
                               interconnection):
        """Update information for the specified interconnection."""
        interconnection_data = interconnection['interconnection']
        with db_api.autonested_transaction(context.session):
            interconnection_obj = self._get_interconnection(context,
                                                            interconnection_id)
            original_interconnection = copy.deepcopy(interconnection_obj)
            interconnection_obj.update(**interconnection_data)

            payload = events.DBEventPayload(context,
                                            resource_id=interconnection_id,
                                            states=(original_interconnection,),
                                            desired_state=interconnection_obj,
                                            request_body=interconnection_data)
            registry.notify(
                inter_consts.INTERCONNECTION, events.PRECOMMIT_UPDATE, self,
                payload=payload)

        payload = inter_callbacks.InterconnectionPayload(
            context, interconnection_obj.id,
            original_interconnection=original_interconnection,
            current_interconnection=interconnection_obj)
        registry.notify(
            inter_consts.INTERCONNECTION, events.AFTER_UPDATE, self,
            payload=payload)

        return interconnection_obj

    def delete_interconnection(self, context, interconnection_id):
        """Delete the specified interconnection."""
        with db_api.autonested_transaction(context.session):
            interconnection_obj = self._get_interconnection(context,
                                                            interconnection_id)
            interconnection_obj.delete()

            payload = inter_callbacks.InterconnectionPayload(
                context, interconnection_obj.id,
                original_interconnection=interconnection_obj)
            registry.notify(
                inter_consts.INTERCONNECTION, events.PRECOMMIT_DELETE, self,
                payload=payload)

        registry.notify(
            inter_consts.INTERCONNECTION, events.AFTER_DELETE, self,
            payload=payload)

    @db_base_plugin_common.filter_fields
    @db_base_plugin_common.convert_result_to_dict
    def get_interconnection(self, context, interconnection_id, fields=None):
        """Return details for the specified interconnection."""
        return self._get_interconnection(context, interconnection_id)

    @db_base_plugin_common.filter_fields
    @db_base_plugin_common.convert_result_to_dict
    def get_interconnections(self, context, filters=None, fields=None,
                             sorts=None, limit=None, marker=None,
                             page_reverse=False):
        """Return details for available interconnections."""
        filters = filters or {}
        pager = objects_base.Pager(sorts=sorts, limit=limit,
                                   page_reverse=page_reverse, marker=marker)
        return inter_objs.Interconnection.get_objects(context, _pager=pager,
                                                      **filters)

    def refresh(self, context, interconnection_id, interconnection=None):
        with db_api.autonested_transaction(context.session):
            interconnection_obj = self._get_interconnection(context,
                                                            interconnection_id)

            fsm = lifecycle_fsm.LifecycleFSM(self.drivers, interconnection_obj)
            if fsm.is_actionable_event('refresh_requested'):
                fsm.process_event('refresh_requested')
