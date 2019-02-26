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

from neutron_interconnection._i18n import _

remote_keystone_auth_opts = [
    cfg.StrOpt('username',
               help=_('Remote Keystone authentication username')),
    cfg.StrOpt('password', secret=True,
               help=_('Remote Keystone authentication password')),
    cfg.StrOpt('project',
               help=_('Remote Keystone authentication project')),
    cfg.IntOpt('check_state_interval', default=10,
               help=_('Check state interval in seconds.')),
]

state_scheduler_opts = [
    cfg.IntOpt('check_state_interval', default=10,
               help=_('Check state interval in seconds.')),
]

cfg.CONF.register_opts(remote_keystone_auth_opts, "remote_keystone_auth")
cfg.CONF.register_opts(state_scheduler_opts, "state_scheduler")
