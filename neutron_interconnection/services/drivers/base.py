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

import abc
import stevedore

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron_lib.api.definitions import interconnection as inter_api_def
from neutron_lib.callbacks import events
from neutron_lib.callbacks import registry

from neutron_interconnection.services.common import constants as inter_consts

LOG = logging.getLogger(__name__)


# prefix for setuptools entry points for interconnection drivers
INTERCONNECTION_DRIVER_ENTRY_POINT_PREFIX = "neutron_interconnection.driver"


def register_drivers():
    drivers = {}
    for interconnection_type in inter_api_def. VALID_TYPES:
        driver_name = cfg.CONF.drivers.get(
            interconnection_type + '_driver')

        LOG.debug("Registering interconnection driver for %s, with %s",
                  interconnection_type, driver_name)
        try:
            driver_class = stevedore.driver.DriverManager(
                namespace='%s.%s' % (
                    INTERCONNECTION_DRIVER_ENTRY_POINT_PREFIX,
                    interconnection_type
                ),
                name=driver_name,
            ).driver

            drivers[interconnection_type] = driver_class()
        except Exception:
            LOG.exception("Error while registering interconnection driver "
                          "for %s with %s", interconnection_type, driver_name)
            raise

    return drivers


@registry.has_registry_receivers
class InterconnectionDriverBase(object):

    name = None

    @registry.receives(inter_consts.INTERCONNECTION,
                       [events.AFTER_CREATE, events.AFTER_DELETE])
    def handle_interconnection_event(self, resource, event, trigger, payload):
        LOG.debug("handle_interconnection_event called with: {resource: %s, "
                  "payload: %s, event: %s",
                  resource, payload, event)
        if event == events.AFTER_CREATE:
            interconnection_obj = payload.current_interconnection
            self.process_interconnection_create(interconnection_obj)
        elif event == events.AFTER_DELETE:
            interconnection_obj = payload.original_interconnection
            self.process_interconnection_delete(interconnection_obj)

    @abc.abstractmethod
    @log_helpers.log_method_call
    def process_interconnection_create(self, interconnection_obj):
        """Process interconnection create event."""

    @abc.abstractmethod
    @log_helpers.log_method_call
    def process_interconnection_delete(self, interconnection_obj):
        """Process interconnection delete event."""

    @abc.abstractmethod
    @log_helpers.log_method_call
    def allocate_local_parameters(self, interconnection_obj):
        """Return local parameters allocated for an interconnection."""

    @abc.abstractmethod
    @log_helpers.log_method_call
    def release_local_parameters(self, interconnection_obj):
        """Release local parameters for an interconnection."""

    @abc.abstractmethod
    @log_helpers.log_method_call
    def update_remote_parameters(self, interconnection_obj):
        """Update an interconnection remote parameters."""
