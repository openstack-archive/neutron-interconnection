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
import mock

from webob import exc

from neutron_lib.api.definitions import interconnection as inter_api_def

from neutron.tests.unit.api.v2 import test_base
from neutron.tests.unit.extensions import base as test_extension_base

from neutron_interconnection.extensions import interconnection as inter_ext

INTERCONNECTION_URI = inter_api_def.API_PREFIX[1:] + '/interconnections'


class InterconnectionExtensionTestCase(test_extension_base.ExtensionTestCase):
    fmt = 'json'

    def setUp(self):
        super(InterconnectionExtensionTestCase, self).setUp()
        plural_mappings = {'interconnection': 'interconnections'}
        self.setup_extension(
            '%s.%s' % (inter_ext.NeutronInterconnectionPluginBase.__module__,
                       inter_ext.NeutronInterconnectionPluginBase.__name__),
            inter_api_def.ALIAS,
            inter_ext.Interconnection,
            inter_api_def.API_PREFIX[1:],
            plural_mappings=plural_mappings,
            use_quota=True)

        self.instance = self.plugin.return_value
        self.interconnection_id = test_base._uuid()
        self.project_id = test_base._uuid()
        self.local_resource_id = test_base._uuid()
        self.remote_resource_id = test_base._uuid()

    def test_interconnection_create(self):
        data = {
            'interconnection': {'name': 'fake-interconnection',
                                'project_id': self.project_id,
                                'local_resource_id': self.local_resource_id,
                                'remote_resource_id': self.remote_resource_id,
                                'remote_keystone': 'fake-keystone',
                                'remote_region': 'fake-region'}
            }

        expected_ret_val = copy.deepcopy(data['interconnection'])
        expected_ret_val.update({'type': inter_api_def.NETWORK_L3})
        expected_call_args = copy.copy(expected_ret_val)
        expected_ret_val.update({'id': self.interconnection_id,
                                 'state': 'TO_VALIDATE',
                                 'local_parameters': {},
                                 'remote_parameters': {}
                                 })

        self.instance.create_interconnection.return_value = expected_ret_val

        res = self.api.post(
            test_base._get_path(INTERCONNECTION_URI, fmt=self.fmt),
            self.serialize(data),
            content_type='application/%s' % self.fmt)

        self.assertDictSupersetOf(
            expected_call_args,
            self.instance.create_interconnection.call_args[1][
                'interconnection']['interconnection'])
        self.assertEqual(exc.HTTPCreated.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('interconnection', res)
        self.assertDictSupersetOf(expected_ret_val, res['interconnection'])

    def test_interconnection_create_invalid_type(self):
        data = {
            'interconnection': {'name': 'fake-interconnection',
                                'project_id': self.project_id,
                                'type': 'fake-type',
                                'local_resource_id': self.local_resource_id,
                                'remote_resource_id': self.remote_resource_id,
                                'remote_keystone': 'fake-keystone',
                                'remote_region': 'fake-region'}
            }

        res = self.api.post(
            test_base._get_path(INTERCONNECTION_URI, fmt=self.fmt),
            self.serialize(data),
            content_type='application/%s' % self.fmt,
            expect_errors=True)

        self.assertEqual(exc.HTTPBadRequest.code, res.status_int)

    def test_interconnection_list(self):
        return_value = [{'id': self.interconnection_id,
                         'name': 'fake-interconnection',
                         'project_id': self.project_id,
                         'type': inter_api_def.NETWORK_L3,
                         'state': 'TO_VALIDATE',
                         'local_resource_id': self.local_resource_id,
                         'remote_resource_id': self.remote_resource_id,
                         'remote_keystone': 'fake-keystone',
                         'remote_region': 'fake-region',
                         'local_parameters': {},
                         'remote_parameters': {}}]

        self.instance.get_interconnections.return_value = return_value

        res = self.api.get(
            test_base._get_path(INTERCONNECTION_URI, fmt=self.fmt))

        self.instance.get_interconnections.assert_called_with(
            mock.ANY, fields=mock.ANY, filters=mock.ANY
        )
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('interconnections', res)
        self.assertEqual(return_value, res['interconnections'])

    def test_interconnection_update(self):
        update_data = {'interconnection': {'name': 'interconnection_updated'}}
        return_value = {'id': self.interconnection_id,
                        'name': 'interconnection_updated',
                        'project_id': self.project_id,
                        'type': inter_api_def.NETWORK_L3,
                        'state': 'TO_VALIDATE',
                        'local_resource_id': self.local_resource_id,
                        'remote_resource_id': self.remote_resource_id,
                        'remote_keystone': 'fake-keystone',
                        'remote_region': 'fake-region',
                        'local_parameters': {},
                        'remote_parameters': {}}

        self.instance.update_interconnection.return_value = return_value

        res = self.api.put(test_base._get_path(INTERCONNECTION_URI,
                                               id=self.interconnection_id,
                                               fmt=self.fmt),
                           self.serialize(update_data),
                           content_type='application/%s' % self.fmt)

        self.instance.update_interconnection.assert_called_with(
            mock.ANY, self.interconnection_id, interconnection=update_data
        )

        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('interconnection', res)
        self.assertEqual(return_value, res['interconnection'])

    def test_interconnection_get(self):
        return_value = {'id': self.interconnection_id,
                        'name': 'interconnection_updated',
                        'project_id': self.project_id,
                        'type': 'router',
                        'state': 'TO_VALIDATE',
                        'local_resource_id': self.local_resource_id,
                        'remote_resource_id': self.remote_resource_id,
                        'remote_keystone': 'fake-keystone',
                        'remote_region': 'fake-region',
                        'local_parameters': {},
                        'remote_parameters': {}}

        self.instance.get_interconnection.return_value = return_value

        res = self.api.get(test_base._get_path(INTERCONNECTION_URI,
                                               id=self.interconnection_id,
                                               fmt=self.fmt))

        self.instance.get_interconnection.assert_called_with(
            mock.ANY, self.interconnection_id, fields=mock.ANY
        )
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIn('interconnection', res)
        self.assertEqual(return_value, res['interconnection'])

    def test_interconnection_delete(self):
        self._test_entity_delete('interconnection')

    def test_interconnection_refresh(self):
        self.instance.refresh.return_value = None

        res = self.api.put(test_base._get_path(INTERCONNECTION_URI,
                                               id=self.interconnection_id,
                                               action='refresh'))

        self.instance.refresh.assert_called_with(
            mock.ANY, self.interconnection_id
        )
        self.assertEqual(exc.HTTPOk.code, res.status_int)
        res = self.deserialize(res)
        self.assertIsNone(res)
