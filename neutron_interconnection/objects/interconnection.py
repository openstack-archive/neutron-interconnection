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

from oslo_serialization import jsonutils
from oslo_versionedobjects import fields as obj_fields

from neutron.objects import base
from neutron.objects import common_types

from neutron_lib.api.definitions import interconnection as inter_api_def

from neutron_interconnection.db import interconnection_db as inter_db
from neutron_interconnection.services.common import constants as inter_consts


class InterconnectionTypeField(obj_fields.AutoTypedField):
    AUTO_TYPE = obj_fields.Enum(valid_values=inter_api_def.VALID_TYPES)


class InterconnectionStateField(obj_fields.AutoTypedField):
    AUTO_TYPE = obj_fields.Enum(valid_values=inter_consts.VALID_STATES)


@base.NeutronObjectRegistry.register
class Interconnection(base.NeutronDbObject):
    # Version 1.0: Initial version
    VERSION = '1.0'

    new_facade = True
    db_model = inter_db.Interconnection

    fields = {
        'id': common_types.UUIDField(),
        'project_id': obj_fields.StringField(),
        'name': obj_fields.StringField(),
        'type': InterconnectionTypeField(),
        'state': InterconnectionStateField(default=inter_consts.PRE_VALIDATE),
        'local_resource_id': common_types.UUIDField(),
        'remote_resource_id': common_types.UUIDField(),
        'remote_keystone': obj_fields.StringField(),
        'remote_region': obj_fields.StringField(),
        'remote_interconnection_id': common_types.UUIDField(nullable=True),
        'local_parameters': obj_fields.DictOfStringsField(default={}),
        'remote_parameters': obj_fields.DictOfStringsField(default={})
    }

    fields_no_update = ['id',
                        'project_id',
                        'type',
                        'local_resource_id',
                        'remote_resource_id',
                        'remote_keystone',
                        'remote_region']

    extra_filter_names = set(['state',
                              'local_resource_id',
                              'remote_resource_id'])

    def update(self, **kwargs):
        self.update_fields(kwargs)
        super(Interconnection, self).update()

    @staticmethod
    def _filter_dict_fields(fields):
        return (f for f in ['local_parameters', 'remote_parameters']
                if f in fields)

    @classmethod
    def modify_fields_from_db(cls, db_obj):
        fields = super(Interconnection, cls).modify_fields_from_db(db_obj)

        for field in cls._filter_dict_fields(fields):
            fields[field] = jsonutils.loads(fields[field])

        return fields

    @classmethod
    def modify_fields_to_db(cls, fields):
        fields = super(Interconnection, cls).modify_fields_to_db(fields)

        for field in cls._filter_dict_fields(fields):
            fields[field] = cls.filter_to_json_str(fields[field])

        return fields
