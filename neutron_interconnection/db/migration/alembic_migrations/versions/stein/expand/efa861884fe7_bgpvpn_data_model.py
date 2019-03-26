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

"""Defining BGPVPN driver data model

Revision ID: efa861884fe7
Revises: 8a3d0c8cc7c0
Create Date: 2018-10-12 16:07:25.867896

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'efa861884fe7'
down_revision = '8a3d0c8cc7c0'


def upgrade():
    op.create_table(
        'interconnection_rtnn_associations',
        sa.Column('interconnection_id', sa.String(length=36), nullable=False),
        sa.Column('rtnn', sa.Integer(), nullable=False),

        sa.PrimaryKeyConstraint('interconnection_id'),
        sa.UniqueConstraint('rtnn')
    )

    op.create_table(
        'interconnection_bgpvpn_associations',
        sa.Column('interconnection_id', sa.String(length=36), nullable=False),
        sa.Column('bgpvpn_id', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('interconnection_id', 'bgpvpn_id')
    )
