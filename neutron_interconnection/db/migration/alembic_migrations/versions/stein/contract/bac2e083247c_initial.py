# Copyright 2018 <PUT YOUR NAME/COMPANY HERE>
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
#

"""contract initial

Revision ID: bac2e083247c
Revises: start_neutron_interconnection
Create Date: 2018-10-12 16:46:02.059688

"""

from neutron.db.migration import cli

# revision identifiers, used by Alembic.
revision = 'bac2e083247c'
down_revision = 'start_neutron_interconnection'
branch_labels = (cli.CONTRACT_BRANCH,)


def upgrade():
    pass
