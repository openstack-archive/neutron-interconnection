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

TO_VALIDATE = 'TO_VALIDATE'

PRE_VALIDATE = 'PRE_VALIDATE'
VALIDATING = 'VALIDATING'
VALIDATED = 'VALIDATED'

PRE_ACTIVATE = 'PRE_ACTIVATE'
ACTIVATING = 'ACTIVATING'
ACTIVE = 'ACTIVE'

PRE_ACTIVE_CHECK = 'PRE_ACTIVE_CHECK'
ACTIVE_CHECKING = 'ACTIVE_CHECKING'

TEARDOWN = 'TEARDOWN'

VALID_STATES = [TO_VALIDATE,
                PRE_VALIDATE, VALIDATING, VALIDATED,
                PRE_ACTIVATE, ACTIVATING, ACTIVE,
                PRE_ACTIVE_CHECK, ACTIVE_CHECKING,
                TEARDOWN]
