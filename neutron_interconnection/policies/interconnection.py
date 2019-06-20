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

from oslo_policy import policy

from neutron_interconnection.policies import base


rules = [
    policy.DocumentedRuleDefault(
        'create_interconnection',
        base.RULE_ADMIN_OR_OWNER,
        'Create an interconnection',
        [
            {
                'method': 'POST',
                'path': '/interconnection/interconnections',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'update_interconnection',
        base.RULE_ADMIN_OR_OWNER,
        'Update an interconnection',
        [
            {
                'method': 'PUT',
                'path': '/interconnection/interconnections/{id}',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'delete_interconnection',
        base.RULE_ADMIN_OR_OWNER,
        'Delete an interconnection',
        [
            {
                'method': 'DELETE',
                'path': '/interconnection/interconnections/{id}',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'get_interconnection',
        base.RULE_ADMIN_OR_OWNER_OR_NEUTRON_INTERCONNECTION_PEER,
        'Get interconnections',
        [
            {
                'method': 'GET',
                'path': '/interconnection/interconnections',
            },
            {
                'method': 'GET',
                'path': '/interconnection/interconnections/{id}',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'get_interconnection:local_parameters',
        base.RULE_ADMIN_OR_NEUTRON_INTERCONNECTION_PEER,
        'Get ``local_parameters`` attributes of interconnections',
        [
            {
                'method': 'GET',
                'path': '/interconnection/interconnections',
            },
            {
                'method': 'GET',
                'path': '/interconnection/interconnections/{id}',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'get_interconnection:remote_parameters',
        base.RULE_ADMIN_OR_NEUTRON_INTERCONNECTION_PEER,
        'Get ``remote_parameters`` attributes of interconnections',
        [
            {
                'method': 'GET',
                'path': '/interconnection/interconnections',
            },
            {
                'method': 'GET',
                'path': '/interconnection/interconnections/{id}',
            },
        ]
    ),

    policy.DocumentedRuleDefault(
        'refresh',
        base.RULE_NEUTRON_INTERCONNECTION_PEER,
        'Refresh an interconnection',
        [
            {
                'method': 'PUT',
                'path': '/interconnection/interconnections/{id}/refresh',
            },
        ]
    ),

]


def list_rules():
    return rules
