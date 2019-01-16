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

from abc import ABCMeta
from abc import abstractmethod

import six

from neutron_lib.api.definitions import interconnection
from neutron_lib.api import extensions as api_extensions
from neutron_lib.services import base as service_base

from neutron.api import extensions
from neutron.api.v2 import resource_helper

from neutron_interconnection import extensions as inter_extensions

extensions.append_api_extensions_path(inter_extensions.__path__)


class Interconnection(api_extensions.APIExtensionDescriptor):

    api_definition = interconnection

    @classmethod
    def get_resources(cls):
        plural_mappings = resource_helper.build_plural_mappings(
            {}, interconnection.RESOURCE_ATTRIBUTE_MAP)
        return resource_helper.build_resource_info(
            plural_mappings,
            interconnection.RESOURCE_ATTRIBUTE_MAP,
            interconnection.ALIAS,
            action_map=interconnection.ACTION_MAP,
            register_quota=True)


@six.add_metaclass(ABCMeta)
class NeutronInterconnectionPluginBase(service_base.ServicePluginBase):

    def get_plugin_type(self):
        return interconnection.ALIAS

    def get_plugin_description(self):
        return 'Neutron-Neutron interconnection service plugin.'

    @abstractmethod
    def create_interconnection(self, context, interconnection):
        pass

    @abstractmethod
    def update_interconnection(self, context, interconnection_id,
                               interconnection):
        pass

    @abstractmethod
    def delete_interconnection(self, context, interconnection_id):
        pass

    @abstractmethod
    def get_interconnections(self, context, filters=None, fields=None,
                             sorts=None, limit=None, marker=None,
                             page_reverse=False):
        pass

    @abstractmethod
    def get_interconnection(self, context, interconnection_id, fields=None):
        pass

    @abstractmethod
    def refresh(self, context, interconnection_id, interconnection=None):
        pass
