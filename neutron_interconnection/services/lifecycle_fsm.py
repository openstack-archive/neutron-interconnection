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

from oslo_log import log

from automaton import machines

from neutronclient.common import exceptions as neutronclient_exc

from neutron_interconnection.services.common import constants as inter_consts
from neutron_interconnection.services.common import utils as inter_utils

LOG = log.getLogger(__name__)


class LifecycleFSM(machines.FiniteMachine):

    def __init__(self, drivers, interconnection_obj):
        super(LifecycleFSM, self).__init__()

        self.drivers = drivers
        self.interconnection_obj = interconnection_obj
        self.neutron_client = inter_utils.get_neutron_client(
            self.interconnection_obj.remote_keystone,
            self.interconnection_obj.remote_region
        )

        self._setup_fsm()

    def _setup_fsm(self):
        # Defines states
        self.add_state(inter_consts.TO_VALIDATE,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.PRE_VALIDATE,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.VALIDATING,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.VALIDATED,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.PRE_ACTIVATE,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.ACTIVATING,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.ACTIVE,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.PRE_ACTIVE_CHECK,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.ACTIVE_CHECKING,
                       on_enter=self.on_enter_update_state_in_db)

        self.add_state(inter_consts.TEARDOWN,
                       terminal=True)

        # Defines states transitions
        self.add_transition(inter_consts.TO_VALIDATE,
                            inter_consts.PRE_VALIDATE,
                            'refresh_requested')
        self.add_transition(inter_consts.TO_VALIDATE,
                            inter_consts.TEARDOWN,
                            'deleted')

        self.add_transition(inter_consts.PRE_VALIDATE,
                            inter_consts.VALIDATING,
                            'lock')

        self.add_transition(inter_consts.VALIDATING,
                            inter_consts.VALIDATED,
                            'symmetric_exist')
        self.add_transition(inter_consts.VALIDATING,
                            inter_consts.TO_VALIDATE,
                            'symmetric_not_found')
        self.add_transition(inter_consts.VALIDATING,
                            inter_consts.PRE_VALIDATE,
                            'retry')

        self.add_transition(inter_consts.VALIDATED,
                            inter_consts.PRE_ACTIVATE,
                            'refresh_requested')
        self.add_transition(inter_consts.VALIDATED,
                            inter_consts.TO_VALIDATE,
                            'symmetric_deleted')
        self.add_transition(inter_consts.VALIDATED,
                            inter_consts.ACTIVE,
                            'activate')
        self.add_transition(inter_consts.VALIDATED,
                            inter_consts.TEARDOWN,
                            'deleted')

        self.add_transition(inter_consts.PRE_ACTIVATE,
                            inter_consts.ACTIVATING,
                            'lock')

        self.add_transition(inter_consts.ACTIVATING,
                            inter_consts.ACTIVE,
                            'symmetric_parameters_received')
        self.add_transition(inter_consts.ACTIVATING,
                            inter_consts.TO_VALIDATE,
                            'symmetric_deleted')
        self.add_transition(inter_consts.ACTIVATING,
                            inter_consts.PRE_ACTIVATE,
                            'retry')

        self.add_transition(inter_consts.ACTIVE,
                            inter_consts.PRE_ACTIVE_CHECK,
                            'refresh_requested')
        self.add_transition(inter_consts.ACTIVE,
                            inter_consts.TO_VALIDATE,
                            'symmetric_deleted')
        self.add_transition(inter_consts.ACTIVE,
                            inter_consts.TEARDOWN,
                            'deleted')

        self.add_transition(inter_consts.PRE_ACTIVE_CHECK,
                            inter_consts.ACTIVE_CHECKING,
                            'lock')

        self.add_transition(inter_consts.ACTIVE_CHECKING,
                            inter_consts.ACTIVE,
                            'symmetric_still_exist')
        self.add_transition(inter_consts.ACTIVE_CHECKING,
                            inter_consts.TO_VALIDATE,
                            'symmetric_deleted')
        self.add_transition(inter_consts.ACTIVE_CHECKING,
                            inter_consts.PRE_ACTIVE_CHECK,
                            'retry')

        # Defines reactions to states transitions
        self.add_reaction(inter_consts.VALIDATING,
                          'lock',
                          self.process_validating)

        self.add_reaction(inter_consts.VALIDATED,
                          'symmetric_exist',
                          self.process_validated)
        self.add_reaction(inter_consts.VALIDATED,
                          'symmetric_not_found',
                          self.process_validated)

        self.add_reaction(inter_consts.ACTIVATING,
                          'lock',
                          self.process_activating)

        self.add_reaction(inter_consts.ACTIVE,
                          'symmetric_parameters_received',
                          self.process_active)

        self.add_reaction(inter_consts.ACTIVE_CHECKING,
                          'lock',
                          self.process_active_checking)

        self.add_reaction(inter_consts.TEARDOWN,
                          'deleted',
                          self.process_teardown)

        # Initialize to interconnection state
        self.initialize(start_state=self.interconnection_obj.state)

    def _post_process_event(self, event, result):
        """Allow to call a reaction callback after state transition."""
        reaction, _ = result
        if reaction:
            callback, args, kwargs = reaction
            callback(event, *args, **kwargs)

    def _set_interconnection_remote_details(self, remote_interconnection):
        self.interconnection_obj.update(
            remote_interconnection_id=remote_interconnection['id'],
            remote_parameters=remote_interconnection.get('local_parameters')
        )

    def _unset_interconnection_remote_details(self):
        self.interconnection_obj.update(remote_interconnection_id=None,
                                        remote_parameters={})

    def _refresh_remote_interconnection(self):
        if self.interconnection_obj.remote_interconnection_id:
            try:
                self.neutron_client.interconnection_refresh(
                    self.interconnection_obj.remote_interconnection_id
                )
            except neutronclient_exc.NotFound:
                self._process_symmetric_not_found()
            except neutronclient_exc.ConnectionFailed:
                LOG.error("Can't connect to remote neutron")
            except neutronclient_exc.Unauthorized:
                LOG.error("Connection refused to remote neutron")

    # Update state in DB when entering new state
    def on_enter_update_state_in_db(self, new_state, trigger_event):
        LOG.debug("Interconnection %s entering state [%s]",
                  self.interconnection_obj.id, new_state)
        self.interconnection_obj.update(state=new_state)

    def _process_symmetric_not_found(self):
        LOG.info("Remote interconnection %s could not be found",
                 self.interconnection_obj.remote_interconnection_id)
        self._unset_interconnection_remote_details()
        # Call driver to release local parameters
        driver = self.drivers[self.interconnection_obj.type]
        driver.release_local_parameters(self.interconnection_obj)
        self.interconnection_obj.update(local_parameters={})
        self.process_event('symmetric_deleted')

    # Transition to VALIDATING state
    def process_validating(self, event_that_triggered, *args, **kwargs):
        filters = {
            'local_resource_id': self.interconnection_obj.remote_resource_id,
            'remote_resource_id': self.interconnection_obj.local_resource_id
        }

        try:
            remote_interconnections = (
                self.neutron_client.list_interconnections(
                    **filters)['interconnections']
            )

            if remote_interconnections:
                remote_interconnection = remote_interconnections.pop()
                self._set_interconnection_remote_details(
                    remote_interconnection)
                self.process_event('symmetric_exist')
            else:
                self.process_event('symmetric_not_found')
        except neutronclient_exc.ConnectionFailed:
            LOG.error("Can't connect to remote neutron")
            self.process_event('retry')
        except neutronclient_exc.Unauthorized:
            LOG.error("Connection refused to remote neutron")
            self.process_event('retry')

    # Transition to VALIDATED state
    def process_validated(self, event_that_triggered):
        if (self.interconnection_obj.local_parameters and
                self.interconnection_obj.remote_parameters):
            self.process_event('activate')
        else:
            # Call driver to allocate local parameters
            driver = self.drivers[self.interconnection_obj.type]
            local_parameters = driver.allocate_local_parameters(
                self.interconnection_obj
            )
            self.interconnection_obj.update(local_parameters=local_parameters)
            self._refresh_remote_interconnection()

    # Transition to ACTIVATING state
    def process_activating(self, event_that_triggered, *args, **kwargs):
        try:
            remote_interconnection = self.neutron_client.show_interconnection(
                self.interconnection_obj.remote_interconnection_id
            )

            self._set_interconnection_remote_details(
                remote_interconnection['interconnection']
            )
            # Call driver to update remote parameters
            driver = self.drivers[self.interconnection_obj.type]
            driver.update_remote_parameters(self.interconnection_obj)
            self.process_event('symmetric_parameters_received')
        except neutronclient_exc.NotFound:
            self._process_symmetric_not_found()
        except neutronclient_exc.ConnectionFailed:
            LOG.error("Can't connect to remote neutron")
            self.process_event('retry')
        except neutronclient_exc.Unauthorized:
            LOG.error("Connection refused to remote neutron")
            self.process_event('retry')

    def process_active(self, event_that_triggered, *args, **kwargs):
        self._refresh_remote_interconnection()

    # Transition ACTIVE_CHECKING state
    def process_active_checking(self, event_that_triggered, *args, **kwargs):

        if not self.interconnection_obj.remote_interconnection_id:
            self.process_event('symmetric_deleted')
            return

        try:
            self.neutron_client.show_interconnection(
                self.interconnection_obj.remote_interconnection_id
            )

            self.process_event('symmetric_still_exist')
        except neutronclient_exc.NotFound:
            self._process_symmetric_not_found()
        except neutronclient_exc.ConnectionFailed:
            LOG.error("Can't connect to remote neutron")
            self.process_event('retry')
        except neutronclient_exc.Unauthorized:
            LOG.error("Connection refused to remote neutron")
            self.process_event('retry')

    # Transition to TEARDOWN state
    def process_teardown(self, event_that_triggered, *args, **kwargs):
        self._refresh_remote_interconnection()
