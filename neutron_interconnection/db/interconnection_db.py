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

import sqlalchemy as sa

from neutron.db import standard_attr

from neutron_lib.api.definitions import interconnection as inter_api_def
from neutron_lib.db import constants as db_const
from neutron_lib.db import model_base

from neutron_interconnection.services.common import constants as inter_consts

KEYSTONE_URL_LEN = 2000
REGION_LEN = 255
PARAMETERS_DICT_LEN = 1024

interconnection_types = sa.Enum(*inter_api_def.VALID_TYPES,
                                name='interconnection_types')

interconnection_states = sa.Enum(*inter_consts.VALID_STATES,
                                 name='interconnection_states')


class Interconnection(standard_attr.HasStandardAttributes, model_base.BASEV2,
                      model_base.HasId, model_base.HasProject):
    """Represents an interconnection object."""
    __tablename__ = 'interconnections'

    __table_args__ = (
        sa.UniqueConstraint(
            'local_resource_id', 'remote_resource_id',
            name='uniq_interconnection0local_resource_id0remote_resource_id'
        ),
        model_base.BASEV2.__table_args__
    )

    name = sa.Column(sa.String(db_const.NAME_FIELD_SIZE))
    type = sa.Column(interconnection_types, nullable=False)
    state = sa.Column(interconnection_states, nullable=False)
    local_resource_id = sa.Column(sa.String(db_const.UUID_FIELD_SIZE),
                                  nullable=False)
    remote_resource_id = sa.Column(sa.String(db_const.UUID_FIELD_SIZE),
                                   nullable=False)
    remote_keystone = sa.Column(sa.String(KEYSTONE_URL_LEN), nullable=False)
    remote_region = sa.Column(sa.String(REGION_LEN), nullable=False)
    remote_interconnection_id = sa.Column(sa.String(db_const.UUID_FIELD_SIZE))
    local_parameters = sa.Column(sa.String(PARAMETERS_DICT_LEN))
    remote_parameters = sa.Column(sa.String(PARAMETERS_DICT_LEN))

    # standard attributes support:
    api_collections = [inter_api_def.COLLECTION_NAME]
    collection_resource_map = {inter_api_def.COLLECTION_NAME:
                               inter_api_def.RESOURCE_NAME}
