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

from oslo_config import cfg

from keystoneauth1.identity import v3
from keystoneauth1 import session

from neutronclient.v2_0 import client as neutronclient

cfg.CONF.import_group('neutron_interconnection',
                      'neutron_interconnection.services.common.config')


def get_neutron_client(keystone_endpoint, region):
    # Use keystone session because Neutron is not yet fully integrated with
    # Keystone v3 API
    auth = v3.Password(
        username=cfg.CONF.neutron_interconnection.username,
        password=cfg.CONF.neutron_interconnection.password,
        project_name=cfg.CONF.neutron_interconnection.project,
        auth_url=keystone_endpoint,
        user_domain_id="default",
        project_domain_id="default"
    )
    sess = session.Session(auth=auth)

    return neutronclient.Client(
        session=sess,
        region_name=region
    )
