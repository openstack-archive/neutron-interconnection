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

import mock
import testtools

from oslo_utils import uuidutils

from neutron_lib.api.definitions import interconnection as inter_api_def
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib import context

from neutron.tests.unit.db import test_db_base_plugin_v2 as test_db_plugin

from neutron_interconnection.objects import interconnection as inter_object
from neutron_interconnection.services.common import callbacks \
    as inter_callbacks
from neutron_interconnection.services.common import constants as inter_consts
from neutron_interconnection.services.common import exceptions as inter_exc
from neutron_interconnection.services import plugin as inter_plugin


def register_mock_callback(resource, event):
    callback = mock.Mock()
    registry.subscribe(callback, resource, event)
    return callback


class TestNeutronInterconnectionPlugin(
        test_db_plugin.NeutronDbPluginV2TestCase):

    def setUp(self):
        super(TestNeutronInterconnectionPlugin, self).setUp()
        self.state_scheduler_patch = (
            mock.patch('neutron_interconnection.services.'
                       'state_scheduler_worker.StateSchedulerWorker').start()
        )
        self.interconnection_plugin = (
            inter_plugin.NeutronInterconnectionPlugin()
        )
        self.mock_neutron_client = mock.Mock()
        self.mock_neutron_client.list_interconnections.return_value = {
            'interconnections': []
        }
        mock.patch('neutronclient.v2_0.client.Client',
                   return_value=self.mock_neutron_client).start()

        self.context = context.get_admin_context()

    def _create_test_interconnection(self):
        interconnection = {'project_id': uuidutils.generate_uuid(),
                           'name': 'fake-interconnection',
                           'type': inter_api_def.NETWORK_L3,
                           'local_resource_id': uuidutils.generate_uuid(),
                           'remote_resource_id': uuidutils.generate_uuid(),
                           'remote_keystone': 'fake-keystone-url',
                           'remote_region': 'fake-region'}
        response = (
            self.interconnection_plugin.create_interconnection(
                self.context, {'interconnection': interconnection})
        )
        return response

    def _get_interconnection_obj(self, interconnection_id):
        return inter_object.Interconnection.get_object(self.context,
                                                       id=interconnection_id)

    def _test_interconnection_create_notify(self, event):
        callback = register_mock_callback(inter_consts.INTERCONNECTION, event)
        interconnection = self._create_test_interconnection()
        interconnection_obj = (
            self._get_interconnection_obj(interconnection['id'])
        )
        payload = inter_callbacks.InterconnectionPayload(
            self.context, interconnection['id'],
            current_interconnection=interconnection_obj)
        callback.assert_called_once_with(
            inter_consts.INTERCONNECTION, event, self.interconnection_plugin,
            payload=payload)

    def test_create_interconnection_notify_after_create(self):
        self._test_interconnection_create_notify(events.AFTER_CREATE)

    def test_create_interconnection_notify_precommit_create(self):
        self._test_interconnection_create_notify(events.PRECOMMIT_CREATE)

    def test_create_interconnection_incompatible_type(self):
        self.mock_neutron_client.list_interconnections.return_value = {
            'interconnections': [{
                'project_id': uuidutils.generate_uuid(),
                'name': 'fake-symmetric-interconnection',
                'type': inter_api_def.NETWORK_L2,
                'local_resource_id': uuidutils.generate_uuid(),
                'remote_resource_id': uuidutils.generate_uuid(),
                'remote_keystone': 'fake-symmetric-keystone-url',
                'remote_region': 'fake-symmetric-region'
            }]
        }

        with testtools.ExpectedException(
                inter_exc.IncompatibleInterconnectionType):
            self._create_test_interconnection()

    def _test_interconnection_update_notify(self, event):
        callback = register_mock_callback(inter_consts.INTERCONNECTION, event)
        interconnection = self._create_test_interconnection()
        orig_interconnection_obj = (
            self._get_interconnection_obj(interconnection['id'])
        )
        interconnection_req = {'interconnection': {'name': 'foo'}}
        self.interconnection_plugin.update_interconnection(
            self.context, interconnection['id'], interconnection_req)
        interconnection_obj = (
            self._get_interconnection_obj(interconnection['id'])
        )
        payload = inter_callbacks.InterconnectionPayload(
            self.context, interconnection['id'],
            original_interconnection=orig_interconnection_obj,
            current_interconnection=interconnection_obj)
        callback.assert_called_once_with(
            inter_consts.INTERCONNECTION, event, self.interconnection_plugin,
            payload=payload)

    def test_interconnection_update_notify_after_update(self):
        self._test_interconnection_update_notify(events.AFTER_UPDATE)

    def test_interconnection_update_notify_precommit_update(self):
        callback = register_mock_callback(inter_consts.INTERCONNECTION,
                                          events.PRECOMMIT_UPDATE)
        interconnection = self._create_test_interconnection()
        orig_interconnection_obj = (
            self._get_interconnection_obj(interconnection['id'])
        )
        interconnection_req = {'interconnection': {'name': 'foo'}}
        self.interconnection_plugin.update_interconnection(
            self.context, interconnection['id'], interconnection_req)
        interconnection_obj = (
            self._get_interconnection_obj(interconnection['id'])
        )
        callback.assert_called_once_with(
            inter_consts.INTERCONNECTION, events.PRECOMMIT_UPDATE,
            self.interconnection_plugin, payload=mock.ANY)
        call_payload = callback.call_args[1]['payload']
        self.assertEqual(orig_interconnection_obj, call_payload.states[0])
        self.assertEqual(interconnection_obj, call_payload.desired_state)

    def _test_interconnection_delete_notify(self, event):
        callback = register_mock_callback(inter_consts.INTERCONNECTION, event)
        interconnection = self._create_test_interconnection()
        interconnection_obj = (
            self._get_interconnection_obj(interconnection['id'])
        )
        self.interconnection_plugin.delete_interconnection(
            self.context, interconnection['id'])
        payload = inter_callbacks.InterconnectionPayload(
            self.context, interconnection['id'],
            original_interconnection=interconnection_obj)
        callback.assert_called_once_with(
            inter_consts.INTERCONNECTION, event, self.interconnection_plugin,
            payload=payload)

    def test_delete_interconnection_notify_after_delete(self):
        self._test_interconnection_delete_notify(events.AFTER_DELETE)

    def test_delete_interconnection_notify_precommit_delete(self):
        self._test_interconnection_delete_notify(events.PRECOMMIT_DELETE)
