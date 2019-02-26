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

from oslo_config import cfg

from neutron.common import utils
from neutron.tests import base

from neutron_interconnection.objects import interconnection as inter_objs
from neutron_interconnection.services import state_scheduler_worker


class StateSchedulerWorkerTestCase(base.BaseTestCase):

    def setUp(self):
        super(StateSchedulerWorkerTestCase, self).setUp()

        cfg.CONF.set_override(
            "check_state_interval", 1, group="state_scheduler"
        )
        self.fsm_mock = mock.Mock()
        self.fsm_mock.process_event = mock.Mock()
        mock.patch(
            'neutron_interconnection.services.lifecycle_fsm.LifecycleFSM',
            return_value=self.fsm_mock
        ).start()

    @mock.patch.object(inter_objs.Interconnection, 'get_objects',
                       side_effect=[None, None,
                                    ["fake-interconnection"],
                                    None, ["fake-interconnection"],
                                    None, None])
    def test_state_scheduler_worker_lifecycle(self, get_objects_mock):
        drivers = mock.Mock()

        worker = state_scheduler_worker.StateSchedulerWorker(
            drivers)
        self.addCleanup(worker.stop)

        worker.start()

        # Any interconnection in xxxxING and PRE_xxxx states
        utils.wait_until_true(
            lambda: get_objects_mock.call_count == 2,
            timeout=5,
            exception=RuntimeError("get_objects_mock not called"))
        self.fsm_mock.process_event.assert_not_called()

        get_objects_mock.reset_mock()
        self.fsm_mock.reset_mock()

        # An interconnection in xxxxING state
        utils.wait_until_true(
            lambda: get_objects_mock.called,
            timeout=5,
            exception=RuntimeError("get_objects_mock not called"))
        self.fsm_mock.process_event.assert_called_once_with("retry")

        get_objects_mock.reset_mock()
        self.fsm_mock.reset_mock()

        # An interconnection in PRE_xxxx state
        utils.wait_until_true(
            lambda: get_objects_mock.called,
            timeout=5,
            exception=RuntimeError("get_objects_mock not called"))
        self.fsm_mock.process_event.assert_called_once_with("lock")

        get_objects_mock.reset_mock()
        self.fsm_mock.reset_mock()

        worker.stop()

        worker.wait()
        self.assertFalse(get_objects_mock.called)
        worker.reset()
        utils.wait_until_true(
            lambda: get_objects_mock.call_count == 2,
            timeout=5,
            exception=RuntimeError("get_objects_mock not called"))
        self.fsm_mock.process_event.assert_not_called()
