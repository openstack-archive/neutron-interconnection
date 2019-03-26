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

from oslo_utils import uuidutils

from neutron_lib.api.definitions import interconnection as inter_api_def

from neutron.tests import base

from neutron_interconnection.objects import interconnection as inter_objs
from neutron_interconnection.services.drivers.bgpvpn import db as driver_db
from neutron_interconnection.services.drivers.bgpvpn import driver

INTERCONNECTION_ID = '1c9130ac-f33e-4016-a81b-9227d6be113f'
BGPVPN_ID = 'b15bdc49-162f-4fa5-8ba7-819f40c3c40f'


class BgpvpnDriverTestCase(base.BaseTestCase):

    def setUp(self):
        super(BgpvpnDriverTestCase, self).setUp()

        # Mock BGPVPN service plugin
        self.mock_bgpvpn_plugin = (
            mock.patch('neutron_lib.plugins.directory'
                       '.get_plugin').start().return_value
        )

        # Mock Route Target allocator
        self.mock_rt_allocator = (
            mock.patch.object(driver_db, 'RTAllocator').start().return_value
        )
        self.mock_rt_allocator.allocate_rt.return_value = 'RT1'

        self.bgpvpn_driver = driver.BgpvpnDriver()

    def _fake_interconnection_obj(self, type=inter_api_def.NETWORK_L3,
                                  local_parameters=None,
                                  remote_parameters=None):
        return inter_objs.Interconnection(**dict(
            id=INTERCONNECTION_ID,
            project_id='fake-project',
            name='fake-interconnection',
            type=type,
            local_resource_id=uuidutils.generate_uuid(),
            remote_resource_id=uuidutils.generate_uuid(),
            remote_interconnection_id=uuidutils.generate_uuid(),
            remote_keystone='fake-keystone-url',
            remote_region='fake-region',
            local_parameters=local_parameters or {},
            remote_parameters=remote_parameters or {})
        )

    @mock.patch.object(driver_db.BgpvpnDriverDB,
                       'create_interconnection_bgpvpn_assoc')
    def test_allocate_local_parameters(self, mock_create_assoc_db):
        def check_create_bgpvpn(context, bgpvpn):
            db_bgpvpn = bgpvpn['bgpvpn']
            self.assertEqual('l3', db_bgpvpn['type'])
            self.assertEqual([], db_bgpvpn['import_targets'])
            self.assertEqual(['RT1'], db_bgpvpn['export_targets'])
            db_bgpvpn['id'] = BGPVPN_ID
            return db_bgpvpn
        self.mock_bgpvpn_plugin.create_bgpvpn.side_effect = check_create_bgpvpn

        interconnection_obj = self._fake_interconnection_obj()
        self.bgpvpn_driver.allocate_local_parameters(interconnection_obj)

        self.mock_bgpvpn_plugin.create_bgpvpn.assert_called_once()
        mock_create_assoc_db.assert_called_once()

    @mock.patch.object(driver_db.BgpvpnDriverDB,
                       'create_interconnection_bgpvpn_assoc')
    def test_allocate_local_parameters_bgpvpn_l2(self, mock_create_assoc_db):
        def check_create_bgpvpn(context, bgpvpn):
            db_bgpvpn = bgpvpn['bgpvpn']
            self.assertEqual('l2', db_bgpvpn['type'])
            self.assertEqual([], db_bgpvpn['import_targets'])
            self.assertEqual(['RT1'], db_bgpvpn['export_targets'])
            db_bgpvpn['id'] = BGPVPN_ID
            return db_bgpvpn
        self.mock_bgpvpn_plugin.create_bgpvpn.side_effect = check_create_bgpvpn

        interconnection_obj = (
            self._fake_interconnection_obj(type=inter_api_def.NETWORK_L2)
        )

        self.bgpvpn_driver.allocate_local_parameters(interconnection_obj)

        self.mock_bgpvpn_plugin.create_bgpvpn.assert_called_once()
        mock_create_assoc_db.assert_called_once()

    @mock.patch.object(driver_db.BgpvpnDriverDB,
                       'create_interconnection_bgpvpn_assoc')
    def test_allocate_local_parameters_symmetric_exist(self,
                                                       mock_create_assoc_db):
        def check_create_bgpvpn(context, bgpvpn):
            db_bgpvpn = bgpvpn['bgpvpn']
            self.assertEqual('l3', db_bgpvpn['type'])
            self.assertEqual(['RT2'], db_bgpvpn['import_targets'])
            self.assertEqual(['RT1'], db_bgpvpn['export_targets'])
            db_bgpvpn['id'] = BGPVPN_ID
            return db_bgpvpn
        self.mock_bgpvpn_plugin.create_bgpvpn.side_effect = check_create_bgpvpn

        interconnection_obj = (
            self._fake_interconnection_obj(remote_parameters={'bgpvpn': 'RT2'})
        )
        self.bgpvpn_driver.allocate_local_parameters(interconnection_obj)

        self.mock_bgpvpn_plugin.create_bgpvpn.assert_called_once()
        mock_create_assoc_db.assert_called_once()

    @mock.patch.object(
        driver_db.BgpvpnDriverDB,
        'get_bgpvpn_assoc_by_interconnection',
        return_value={'interconnection_id': INTERCONNECTION_ID,
                      'bgpvpn_id': BGPVPN_ID}
    )
    def test_update_remote_parameters(self, mock_get_assoc_db):
        def check_update_bgpvpn(context, bgpvpn_id, bgpvpn):
            db_bgpvpn = bgpvpn['bgpvpn']
            self.assertEqual(['RT2'], db_bgpvpn['import_targets'])
        self.mock_bgpvpn_plugin.update_bgpvpn.side_effect = check_update_bgpvpn

        interconnection_obj = (
            self._fake_interconnection_obj(remote_parameters={'bgpvpn': 'RT2'})
        )
        self.bgpvpn_driver.update_remote_parameters(interconnection_obj)

        self.mock_bgpvpn_plugin.update_bgpvpn.assert_called_once()

    @mock.patch.object(
        driver_db.BgpvpnDriverDB,
        'get_bgpvpn_assoc_by_interconnection',
        return_value={'interconnection_id': INTERCONNECTION_ID,
                      'bgpvpn_id': BGPVPN_ID}
    )
    def test_update_remote_parameters_symmetric_deleted(self,
                                                        mock_get_assoc_db):
        def check_update_bgpvpn(context, bgpvpn_id, bgpvpn):
            db_bgpvpn = bgpvpn['bgpvpn']
            self.assertEqual([], db_bgpvpn['import_targets'])
        self.mock_bgpvpn_plugin.update_bgpvpn.side_effect = check_update_bgpvpn

        interconnection_obj = self._fake_interconnection_obj()
        self.bgpvpn_driver.update_remote_parameters(interconnection_obj)

        self.mock_bgpvpn_plugin.update_bgpvpn.assert_called_once()

    @mock.patch.object(
        driver_db.BgpvpnDriverDB,
        'get_bgpvpn_assoc_by_interconnection',
        return_value={'interconnection_id': INTERCONNECTION_ID,
                      'bgpvpn_id': BGPVPN_ID}
    )
    @mock.patch.object(driver_db.BgpvpnDriverDB,
                       'delete_interconnection_bgpvpn_assoc')
    def test_release_local_parameters(self, mock_get_assoc_db,
                                      mock_delete_assoc_db):
        interconnection_obj = (
            self._fake_interconnection_obj(local_parameters={'bgpvpn': 'RT1'})
        )
        self.bgpvpn_driver.release_local_parameters(interconnection_obj)

        self.mock_rt_allocator.release_rt.assert_called_once_with(
            interconnection_obj.id
        )
        self.mock_bgpvpn_plugin.delete_bgpvpn.assert_called_once()

    def test_release_local_parameters_not_allocated(self):
        interconnection_obj = self._fake_interconnection_obj()
        self.bgpvpn_driver.release_local_parameters(interconnection_obj)

        self.mock_rt_allocator.release_rt.assert_not_called()
        self.mock_bgpvpn_plugin.delete_bgpvpn.assert_not_called()
