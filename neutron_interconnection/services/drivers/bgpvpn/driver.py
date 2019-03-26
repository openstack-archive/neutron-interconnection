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

from oslo_log import log as logging

from neutron_lib.api.definitions import bgpvpn as bgpvpn_api_def
from neutron_lib.api.definitions import interconnection as inter_api_def
from neutron_lib.api.definitions import l3
from neutron_lib import context as n_context
from neutron_lib.plugins import directory

from neutron_interconnection.services.drivers import base as driver_base
from neutron_interconnection.services.drivers.bgpvpn import db as bgpvpn_db

LOG = logging.getLogger(__name__)


class BgpvpnDriver(driver_base.InterconnectionDriverBase,
                   bgpvpn_db.BgpvpnDriverDB):
    """BGPVPN interconnection driver class."""
    name = 'bgpvpn'

    def __init__(self):
        super(BgpvpnDriver, self).__init__()

        self.admin_context = n_context.get_admin_context()
        self.rt_allocator = bgpvpn_db.RTAllocator()

    def _create_bgpvpn(self, interconnection_obj, export_target):
        bgpvpn_plugin = directory.get_plugin(bgpvpn_api_def.ALIAS)

        bgpvpn_type = (
            bgpvpn_api_def.BGPVPN_L3 if interconnection_obj.type in (
                l3.ROUTER, inter_api_def.NETWORK_L3)
            else bgpvpn_api_def.BGPVPN_L2)

        import_rt = interconnection_obj.remote_parameters.get(self.name)

        bgpvpn = bgpvpn_plugin.create_bgpvpn(
            self.admin_context,
            {'bgpvpn': {'tenant_id': interconnection_obj.project_id,
                        'name': 'interconnection:%s' % interconnection_obj.id,
                        'type': bgpvpn_type,
                        'route_targets': [],
                        'import_targets': [import_rt] if import_rt else [],
                        'export_targets': [export_target]}
             }
        )

        return bgpvpn

    def _create_bgpvpn_network_association(self, bgpvpn, network_id):
        bgpvpn_plugin = directory.get_plugin(bgpvpn_api_def.ALIAS)

        network_assoc = bgpvpn_plugin.create_bgpvpn_network_association(
            self.admin_context,
            bgpvpn['id'],
            {'network_association': {'network_id': network_id,
                                     'tenant_id': bgpvpn['tenant_id']}
             }
        )
        LOG.debug("Interconnection network associated to BGPVPN: %s" %
                  network_assoc)

    def _create_bgpvpn_router_association(self, bgpvpn, router_id):
        bgpvpn_plugin = directory.get_plugin(bgpvpn_api_def.ALIAS)

        router_assoc = bgpvpn_plugin.create_bgpvpn_router_association(
            self.admin_context,
            bgpvpn['id'],
            {'router_association': {'router_id': router_id,
                                    'tenant_id': bgpvpn['tenant_id']}
             }
        )
        LOG.debug("Interconnection router associated to BGPVPN: %s" %
                  router_assoc)

    def _update_bgpvpn(self, interconnection_obj):
        bgpvpn_assoc = (
            self.get_bgpvpn_assoc_by_interconnection(self.admin_context,
                                                     interconnection_obj.id)
        )

        if bgpvpn_assoc:
            bgpvpn_plugin = directory.get_plugin(bgpvpn_api_def.ALIAS)

            import_rt = interconnection_obj.remote_parameters.get(self.name)
            bgpvpn_delta = {
                'bgpvpn': {'import_targets': [import_rt] if import_rt else []}
            }

            bgpvpn_plugin.update_bgpvpn(self.admin_context,
                                        bgpvpn_assoc['bgpvpn_id'],
                                        bgpvpn_delta)

    def _delete_bgpvpn(self, bgpvpn_id):
        bgpvpn_plugin = directory.get_plugin(bgpvpn_api_def.ALIAS)
        bgpvpn_plugin.delete_bgpvpn(self.admin_context, bgpvpn_id)

    def _delete_interconnection_bgpvpn_assoc(self, interconnection_id):
        bgpvpn_assoc = (
            self.get_bgpvpn_assoc_by_interconnection(
                self.admin_context, interconnection_id)
        )

        if bgpvpn_assoc:
            self.delete_interconnection_bgpvpn_assoc(
                self.admin_context,
                interconnection_id,
                bgpvpn_assoc['bgpvpn_id']
            )
            self._delete_bgpvpn(bgpvpn_assoc['bgpvpn_id'])

    def process_interconnection_create(self, interconnection_obj):
        pass

    def process_interconnection_delete(self, interconnection_obj):
        if self.name in interconnection_obj.local_parameters:
            self.rt_allocator.release_rt(interconnection_obj.id)
            self._delete_interconnection_bgpvpn_assoc(interconnection_obj.id)

    def allocate_local_parameters(self, interconnection_obj):
        export_target = self.rt_allocator.allocate_rt(interconnection_obj.id)
        bgpvpn = self._create_bgpvpn(interconnection_obj, export_target)
        interconnection_assoc = {'interconnection_id': interconnection_obj.id,
                                 'bgpvpn_id': bgpvpn['id']}
        self.create_interconnection_bgpvpn_assoc(self.admin_context,
                                                 interconnection_assoc)
        LOG.debug("Interconnection associated to BGPVPN: %s" %
                  interconnection_assoc)

        if interconnection_obj.type == l3.ROUTER:
            self._create_bgpvpn_router_association(
                bgpvpn, interconnection_obj.local_resource_id)
        else:
            self._create_bgpvpn_network_association(
                bgpvpn, interconnection_obj.local_resource_id)

        return {self.name: export_target}

    def release_local_parameters(self, interconnection_obj):
        if self.name in interconnection_obj.local_parameters:
            self.rt_allocator.release_rt(interconnection_obj.id)
            self._delete_interconnection_bgpvpn_assoc(interconnection_obj.id)

    def update_remote_parameters(self, interconnection_obj):
        self._update_bgpvpn(interconnection_obj)
