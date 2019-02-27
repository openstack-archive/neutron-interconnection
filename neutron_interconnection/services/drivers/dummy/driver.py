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

from neutron_interconnection.services.drivers import base as driver_base

LOG = logging.getLogger(__name__)


class DummyDriver(driver_base.InterconnectionDriverBase):
    """Dummy interconnection driver class."""
    name = 'dummy'

    def process_interconnection_create(self, interconnection_obj):
        pass

    def process_interconnection_delete(self, interconnection_obj):
        pass

    def allocate_local_parameters(self, interconnection_obj):
        return {self.name: 'dummy:%s' % interconnection_obj.id}

    def release_local_parameters(self, interconnection_obj):
        pass

    def update_remote_parameters(self, interconnection_obj):
        pass
