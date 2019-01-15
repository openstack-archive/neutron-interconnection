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

import random

from oslo_utils import uuidutils

from neutron.tests.unit.objects import test_base
from neutron.tests.unit import testlib_api

from neutron_lib.api.definitions import interconnection as inter_api_def

from neutron_interconnection.objects import interconnection as inter_objs
from neutron_interconnection.services.common import constants as inter_consts

test_base.FIELD_TYPE_VALUE_GENERATOR_MAP[
    inter_objs.InterconnectionTypeField] = (
        lambda: random.choice(inter_api_def.VALID_TYPES)
    )

test_base.FIELD_TYPE_VALUE_GENERATOR_MAP[
    inter_objs.InterconnectionStateField] = (
        lambda: random.choice(inter_consts.VALID_STATES)
    )


class InterconnectionObjectTestCase(test_base.BaseObjectIfaceTestCase):

    _test_class = inter_objs.Interconnection


class InterconnectionDbObjectTestCase(test_base.BaseDbObjectTestCase,
                                      testlib_api.SqlTestCase):

    _test_class = inter_objs.Interconnection

    def test_update_multiple_fields(self):
        interconnection = inter_objs.Interconnection(
            context=self.context,
            name='fake-interconnection',
            type=inter_api_def.NETWORK_L3,
            state=inter_consts.VALIDATED,
            local_resource_id=uuidutils.generate_uuid(),
            remote_resource_id=uuidutils.generate_uuid(),
            remote_keystone='fake-keystone-url',
            remote_region='fake-region'
        )

        interconnection.create()
        fields = {'state': inter_consts.ACTIVE,
                  'local_paramters': {'foo': 45},
                  'remote_parapeters': {'bar': 43}}
        interconnection.update(**fields)

        interconnection = inter_objs.Interconnection.get_object(
            self.context, id=interconnection.id
        )
        self._assert_interconnection_fields(interconnection)

    def _assert_interconnection_fields(self, interconnection, **kwargs):
        for k in interconnection.fields:
            if k in kwargs:
                self.assertEqual(kwargs[k], interconnection[k])
