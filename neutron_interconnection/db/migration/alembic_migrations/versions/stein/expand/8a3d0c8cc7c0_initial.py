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

"""expand initial

Revision ID: 8a3d0c8cc7c0
Revises: start_neutron_interconnection
Create Date: 2018-08-01 17:20:43.229570

"""

from alembic import op
import sqlalchemy as sa

from neutron_lib.api.definitions import interconnection as inter_api_def

from neutron.db.migration import cli

from neutron_interconnection.services.common import constants as inter_consts

# revision identifiers, used by Alembic.
revision = '8a3d0c8cc7c0'
down_revision = 'start_neutron_interconnection'
branch_labels = (cli.EXPAND_BRANCH,)

interconnection_types = sa.Enum(*inter_api_def.VALID_TYPES,
                                name='interconnection_types')

interconnection_states = sa.Enum(*inter_consts.VALID_STATES,
                                 name='interconnection_states')


def upgrade():
    op.create_table(
        'interconnections',
        sa.Column('standard_attr_id', sa.BigInteger(), nullable=True),
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('project_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('type', interconnection_types, nullable=False),
        sa.Column('state', interconnection_states, nullable=False),
        sa.Column('local_resource_id', sa.String(length=36), nullable=False),
        sa.Column('remote_resource_id', sa.String(length=36), nullable=False),
        sa.Column('remote_keystone', sa.String(length=2000), nullable=False),
        sa.Column('remote_region', sa.String(length=255), nullable=False),
        sa.Column('remote_interconnection_id', sa.String(length=36),
                  nullable=True),
        sa.Column('local_parameters', sa.String(length=1024), nullable=True),
        sa.Column('remote_parameters', sa.String(length=1024), nullable=True),

        sa.PrimaryKeyConstraint('id'),

        sa.UniqueConstraint(
            'local_resource_id', 'remote_resource_id',
            name='uniq_interconnection0local_resource_id0remote_resource_id'
        ),
    )
