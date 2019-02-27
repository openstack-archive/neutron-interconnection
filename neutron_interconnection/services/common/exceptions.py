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

from neutron_lib import exceptions as n_exc

from neutron_interconnection._i18n import _


class InterconnectionDriverError(n_exc.NeutronException):
    message = _("Interconnection driver %(method)s call failed.")


class InterconnectionNotFound(n_exc.NotFound):
    message = _("Interconnection %(id)s could not be found.")


class IncompatibleInterconnectionType(n_exc.NeutronException):
    message = _("Interconnection type incompatible with symmetric one")
