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

import datetime

from oslo_config import cfg
from oslo_log import log as logging

from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry
from neutron_lib import context as n_context
from neutron_lib.objects import utils as obj_utils

from neutron import worker as n_worker

from neutron_interconnection.objects import interconnection as inter_objs
from neutron_interconnection.services.common import constants as inter_consts
from neutron_interconnection.services import lifecycle_fsm

# Delta time in seconds from which an interconnection resource has been left
# in in xxxxING (negative value)
CHECK_STATE_DELTA = -600

LOG = logging.getLogger(__name__)


@registry.has_registry_receivers
class StateSchedulerWorker(n_worker.PeriodicWorker):
    """Starts a periodic task to check interconnection resources state.

    This task will look in database if an interconnection resource:
    - has been left in xxxxING state since several seconds,
    - is in PRE_xxxx state.

    Can also be triggered by AFTER_CREATE and AFTER_DELETE database events.
    """

    def __init__(self, drivers):
        super(StateSchedulerWorker, self).__init__(
            self._check_state,
            cfg.CONF.state_scheduler.check_state_interval,
            0)
        self.drivers = drivers

    def _check_state(self):
        admin_context = n_context.get_admin_context()
        state_event = 'retry'

        # Check if an interconnection is in a xxxxING state since
        # several secondes
        time_before = datetime.timedelta(seconds=CHECK_STATE_DELTA)
        interconnection = inter_objs.Interconnection.get_objects(
            admin_context, validate_filters=False,
            count=1, state=obj_utils.StringEnds('ING'),
            changed_since=(datetime.datetime.strftime(
                datetime.datetime.utcnow() + time_before,
                '%Y-%m-%dT%H:%M:%S') + 'Z'
            )
        )

        if not interconnection:
            # Check if an interconnection is in a PRE_xxxx state
            interconnection = inter_objs.Interconnection.get_objects(
                admin_context, validate_filters=False,
                count=1, state=obj_utils.StringStarts('PRE')
            )
            state_event = 'lock'

        if interconnection:
            LOG.debug("Processing interconnection: %s", interconnection[0])
            fsm = lifecycle_fsm.LifecycleFSM(self.drivers, interconnection[0])
            fsm.process_event(state_event)

    @registry.receives(inter_consts.INTERCONNECTION, [events.AFTER_CREATE])
    def process_interconnection_create(self, resource, event, trigger,
                                       payload):
        interconnection_obj = payload.current_interconnection

        fsm = lifecycle_fsm.LifecycleFSM(self.drivers, interconnection_obj)
        if fsm.is_actionable_event('lock'):
            fsm.process_event('lock')

    @registry.receives(inter_consts.INTERCONNECTION, [events.AFTER_DELETE])
    def process_interconnection_delete(self, resource, event, trigger,
                                       payload):
        interconnection_obj = payload.original_interconnection

        fsm = lifecycle_fsm.LifecycleFSM(self.drivers, interconnection_obj)
        if fsm.is_actionable_event('deleted'):
            fsm.process_event('deleted')
