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
from neutron_lib import context

from neutron.tests import base

from neutronclient.common import exceptions as neutronclient_exc

from neutron_interconnection.objects import interconnection as inter_objs
from neutron_interconnection.services.common import constants as inter_consts
from neutron_interconnection.services import lifecycle_fsm


class TestLifecycleFSM(base.BaseTestCase):

    def setUp(self):
        super(TestLifecycleFSM, self).setUp()

        self.ctx = context.get_admin_context()

        mock_driver = mock.Mock()
        mock_driver.allocate_local_parameters.return_value = {'bar': '45'}
        self.mock_drivers = {inter_api_def.NETWORK_L3: mock_driver}

        self.mock_neutron_client = mock.Mock()
        mock.patch('neutronclient.v2_0.client.Client',
                   return_value=self.mock_neutron_client).start()

        mock.patch('neutron.objects.db.api.create_object').start()
        mock.patch('neutron.objects.db.api.update_object').start()

        # We don't use real models as per mocks above. We also need to mock-out
        # methods that work with real data types
        mock.patch(
            'neutron.objects.base.NeutronDbObject.modify_fields_from_db'
        ).start()

    def _fake_interconnection(self, state, remote_interconnection_id=None,
                              local_parameters=None, remote_parameters=None):
        return dict(
            id=uuidutils.generate_uuid(),
            project_id=uuidutils.generate_uuid(),
            name='fake-interconnection',
            type=inter_api_def.NETWORK_L3,
            state=state,
            local_resource_id=uuidutils.generate_uuid(),
            remote_resource_id=uuidutils.generate_uuid(),
            remote_interconnection_id=remote_interconnection_id,
            remote_keystone='fake-keystone-url',
            remote_region='fake-region',
            local_parameters=local_parameters or {},
            remote_parameters=remote_parameters or {}
        )

    def _test_transition_refresh_requested(self, init_state, final_state):
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(init_state)
        )

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('refresh_requested')

        self.assertEqual(final_state, test_fsm.current_state)
        self.assertEqual(final_state, test_interconnection_obj.state)

    def _test_transition_deleted(self, init_state):
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(init_state)
        )

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('deleted')

        self.assertEqual(inter_consts.TEARDOWN,
                         test_fsm.current_state)

        self.mock_neutron_client.interconnection_refresh.called_once()

    def test_transition_to_validate_refresh_requested(self):
        """Test transition from TO_VALIDATE state.

        - Events: refresh_requested
        - Result state: PRE_VALIDATE
        """
        self._test_transition_refresh_requested(
            inter_consts.TO_VALIDATE,
            inter_consts.PRE_VALIDATE
        )

    def test_transition_to_validate_deleted(self):
        """Test transition from TO_VALIDATE state.

        - Events: deleted
        - Result state: TEARDOWN
        """
        self._test_transition_deleted(inter_consts.TO_VALIDATE)

    def test_transition_pre_validate_symmetric_not_found(self):
        """Test transition from PRE_VALIDATE.

        - Events: lock, symmetric_not_found
        - Result state: TO_VALIDATE
        """
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(
                inter_consts.PRE_VALIDATE
            )
        )

        self.mock_neutron_client.list_interconnections.return_value = {
            'interconnections': []
        }

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('lock')

        self.assertEqual(inter_consts.TO_VALIDATE,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.TO_VALIDATE,
                         test_interconnection_obj.state)

    def test_transition_pre_validate_symmetric_exist(self):
        """Test transition from PRE_VALIDATE.

        - Events: lock, symmetric_exist
        - Result state: VALIDATED
        """
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(
                inter_consts.PRE_VALIDATE
            )
        )

        remote_interconnection = self._fake_interconnection(
            inter_consts.VALIDATED,
            remote_interconnection_id=uuidutils.generate_uuid(),
            local_parameters={'foo': '43'}
        )

        self.mock_neutron_client.list_interconnections.return_value = {
            'interconnections': [remote_interconnection]
        }

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('lock')

        self.assertEqual(inter_consts.VALIDATED,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.VALIDATED,
                         test_interconnection_obj.state)

        self.assertEqual(remote_interconnection['id'],
                         test_interconnection_obj.remote_interconnection_id)
        self.assertEqual(remote_interconnection['local_parameters'],
                         test_interconnection_obj.remote_parameters)
        self.assertEqual({'bar': '45'},
                         test_interconnection_obj.local_parameters)

        self.mock_neutron_client.interconnection_refresh.assert_called_once()

    def test_transition_pre_validate_exception_raised(self):
        """Test transition from PRE_VALIDATE.

        - Events: lock
        - Raised exception: neutronclient.common.exceptions.ConnectionFailed
        - Result state: PRE_VALIDATE
        """
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(
                inter_consts.PRE_VALIDATE
            )
        )

        self.mock_neutron_client.list_interconnections.side_effect = (
            neutronclient_exc.ConnectionFailed()
        )

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('lock')

        self.assertEqual(inter_consts.PRE_VALIDATE,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.PRE_VALIDATE,
                         test_interconnection_obj.state)

    def test_transition_pre_validate_activate(self):
        """Test transition from PRE_VALIDATE.

        - Events: lock, symetric_exist, activate
        - Result state: ACTIVE
        """
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(
                inter_consts.PRE_VALIDATE,
                local_parameters={'bar': '45'}
            )
        )

        remote_interconnection = self._fake_interconnection(
            inter_consts.VALIDATED,
            remote_interconnection_id=uuidutils.generate_uuid(),
            local_parameters={'foo': '43'}
        )

        self.mock_neutron_client.list_interconnections.return_value = {
            'interconnections': [remote_interconnection]
        }

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('lock')

        self.assertEqual(inter_consts.ACTIVE,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.ACTIVE,
                         test_interconnection_obj.state)
        self.assertEqual(remote_interconnection['id'],
                         test_interconnection_obj.remote_interconnection_id)
        self.assertEqual(remote_interconnection['local_parameters'],
                         test_interconnection_obj.remote_parameters)

        self.mock_neutron_client.interconnection_refresh.assert_not_called()

    def test_transition_validated_refresh_requested(self):
        """Test transition from VALIDATED state.

        - Events: refresh_requested
        - Result state: PRE_ACTIVATE
        """
        self._test_transition_refresh_requested(
            inter_consts.VALIDATED,
            inter_consts.PRE_ACTIVATE
        )

    def test_transition_validated_deleted(self):
        """Test transition from VALIDATED state.

        - Events: deleted
        - Result state: TEARDOWN
        """
        self._test_transition_deleted(inter_consts.VALIDATED)

    def test_transition_pre_activate_symmetric_deleted(self):
        """Test transition from PRE_ACTIVATE.

        - Events: lock, symmetric_deleted
        - Raised exception: neutronclient.common.exceptions.NotFound
        - Result state: TO_VALIDATED
        """
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(
                inter_consts.PRE_ACTIVATE
            )
        )

        self.mock_neutron_client.show_interconnection.side_effect = (
            neutronclient_exc.NotFound()
        )

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('lock')

        self.assertEqual(inter_consts.TO_VALIDATE,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.TO_VALIDATE,
                         test_interconnection_obj.state)

    def test_transition_pre_activate_symmetric_parameters_received(self):
        """Test transition from PRE_ACTIVATE.

        - Events: lock, symmetric_parameters_received
        - Result state: ACTIVE
        """
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(
                inter_consts.PRE_ACTIVATE,
                local_parameters={'bar': '45'}
            )
        )

        remote_interconnection = self._fake_interconnection(
            inter_consts.ACTIVE,
            remote_interconnection_id=uuidutils.generate_uuid(),
            local_parameters={'foo': '43'},
            remote_parameters={'bar': '45'}
        )

        self.mock_neutron_client.show_interconnection.return_value = {
            'interconnection': remote_interconnection
        }

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('lock')

        self.assertEqual(inter_consts.ACTIVE,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.ACTIVE,
                         test_interconnection_obj.state)

    def test_transition_active_refresh_requested(self):
        """Test transition from ACTIVE state.

        - Events: refresh_requested
        - Result state: PRE_ACTIVE_CHECK
        """
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(inter_consts.ACTIVE)
        )

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('refresh_requested')

        self.assertEqual(inter_consts.PRE_ACTIVE_CHECK,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.PRE_ACTIVE_CHECK,
                         test_interconnection_obj.state)

    def test_transition_active_deleted(self):
        """Test transition from ACTIVE state.

        - Events: deleted
        - Result state: TEARDOWN
        """
        self._test_transition_deleted(inter_consts.ACTIVE)

    def test_transition_pre_active_check_symmetric_deleted(self):
        """Test transition from PRE_ACTIVE_CHECK state.

        - Events: lock, symmetric_deleted
        - Result state: TO_VALIDATE
        """
        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(
                inter_consts.PRE_ACTIVE_CHECK,
                remote_interconnection_id=uuidutils.generate_uuid(),
                local_parameters={'bar': '45'},
                remote_parameters={'foo': '43'}
            )
        )

        self.mock_neutron_client.show_interconnection.side_effect = (
            neutronclient_exc.NotFound()
        )

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('lock')

        self.assertEqual(inter_consts.TO_VALIDATE,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.TO_VALIDATE,
                         test_interconnection_obj.state)
        self.assertIsNone(test_interconnection_obj.remote_interconnection_id)
        self.assertTrue(not test_interconnection_obj.remote_parameters)

    def test_transition_pre_active_check_symmetric_still_exist(self):
        """Test transition from PRE_ACTIVE_CHECK state.

        - Events: lock, symmetric_still_exist
        - Result state: ACTIVE
        """
        remote_interconnection = self._fake_interconnection(
            inter_consts.ACTIVE,
            remote_interconnection_id=uuidutils.generate_uuid(),
            local_parameters={'foo': '43'},
            remote_parameters={'bar': '45'}
        )

        test_interconnection_obj = inter_objs.Interconnection(
            self.ctx,
            **self._fake_interconnection(
                inter_consts.PRE_ACTIVE_CHECK,
                remote_interconnection_id=remote_interconnection['id'],
                local_parameters=remote_interconnection['remote_parameters'],
                remote_parameters=remote_interconnection['local_parameters']
            )
        )

        self.mock_neutron_client.show_interconnection.return_value = {
            'interconnection': remote_interconnection
        }

        test_interconnection_obj.create()
        test_fsm = lifecycle_fsm.LifecycleFSM(self.mock_drivers,
                                              test_interconnection_obj)
        test_fsm.process_event('lock')

        self.assertEqual(inter_consts.ACTIVE,
                         test_fsm.current_state)

        self.assertEqual(inter_consts.ACTIVE,
                         test_interconnection_obj.state)
