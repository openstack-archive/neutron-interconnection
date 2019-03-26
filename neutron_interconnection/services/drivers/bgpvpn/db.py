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

import six
import sqlalchemy as sa

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron_lib import context as n_context
from neutron_lib.db import api as db_api
from neutron_lib.db import model_base

from neutron_interconnection._i18n import _

LOG = logging.getLogger(__name__)

bgpvpn_driver_opts = [
    cfg.IntOpt('bgpvpn_as_number', default=64512,
               help=_("Autonomous System number used to generate BGP Route "
                      "Targets that will be used for BGPVPN allocations")),
    cfg.ListOpt('bgpvpn_rtnn',
                default=[3000, 3999],
                help=_("List containing <rtnn_min>, <rtnn_max> "
                       "defining a range of BGP Route Targets that will "
                       "be used for BGPVPN allocations.")),
]

cfg.CONF.register_opts(bgpvpn_driver_opts, "bgpvpn_driver")


class InterconnectionRTAssoc(model_base.BASEV2):
    """Mapping from an interconnection to NN part of an AS:NN route target."""

    __tablename__ = 'interconnection_rtnn_associations'
    interconnection_id = sa.Column(sa.String(36), primary_key=True)
    rtnn = sa.Column(sa.Integer, unique=True, nullable=False)


def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


@singleton
class RTAllocator(object):
    def __init__(self):
        self.config = cfg.CONF.bgpvpn_driver
        self.session = n_context.get_admin_context().session

    def _get_rt_from_rtnn(self, rtnn):
        return ':'.join([str(self.config.bgpvpn_as_number), str(rtnn)])

    @log_helpers.log_method_call
    def allocate_rt(self, interconnection_id):
        query = self.session.query(
            InterconnectionRTAssoc).order_by(
            InterconnectionRTAssoc.rtnn)

        allocated_rtnns = {obj.rtnn for obj in query.all()}

        # Find first one available in range
        start = int(self.config.bgpvpn_rtnn[0])
        end = int(self.config.bgpvpn_rtnn[1]) + 1
        for rtnn in six.moves.range(start, end):
            if rtnn not in allocated_rtnns:
                with self.session.begin(subtransactions=True):
                    assoc_rtnn = InterconnectionRTAssoc(
                        interconnection_id=interconnection_id,
                        rtnn=rtnn
                    )
                    self.session.add(assoc_rtnn)
                return self._get_rt_from_rtnn(rtnn)

        LOG.error("Can't allocate route target, all range in use")
        return None

    @log_helpers.log_method_call
    def release_rt(self, interconnection_id):
        with self.session.begin(subtransactions=True):
            assoc_rtnn = self.session.query(
                InterconnectionRTAssoc).filter_by(
                interconnection_id=interconnection_id).first()

            if assoc_rtnn:
                self.session.delete(assoc_rtnn)
            else:
                LOG.warning("Can't release route target %s, not used",
                            assoc_rtnn)


class InterconnectionBGPVPNAssoc(model_base.BASEV2):
    """BGPVPN interconnection association table.

    It represents the association table which associate bgpvpns with
    interconnections.
    """
    __tablename__ = 'interconnection_bgpvpn_associations'
    interconnection_id = sa.Column(sa.String(36),
                                   primary_key=True)
    bgpvpn_id = sa.Column(sa.String(36),
                          primary_key=True)


class BgpvpnDriverDB(object):

    def _make_interconnection_bgpvpn_assoc_dict(self, assoc, fields=None):
        res = {'interconnection_id': assoc['interconnection_id'],
               'bgpvpn_id': assoc['bgpvpn_id']
               }

        return self._fields(res, fields)

    def create_interconnection_bgpvpn_assoc(self, context, assoc):
        with db_api.CONTEXT_WRITER.using(context):
            args = self._filter_non_model_columns(assoc,
                                                  InterconnectionBGPVPNAssoc)
            assoc_obj = InterconnectionBGPVPNAssoc(**args)
            context.session.add(assoc_obj)
            return self._make_interconnection_bgpvpn_assoc_dict(assoc_obj)

    def delete_interconnection_bgpvpn_assoc(self, context, interconnection_id,
                                            bgpvpn_id):
        with db_api.CONTEXT_WRITER.using(context):
            context.session.query(InterconnectionBGPVPNAssoc).filter_by(
                interconnection_id=interconnection_id, bgpvpn_id=bgpvpn_id
            ).delete()

    def get_bgpvpn_assoc_by_interconnection(self, context, interconnection_id):
        with db_api.CONTEXT_READER.using(context):
            qry = context.session.query(InterconnectionBGPVPNAssoc)
            qry.filter_by(interconnection_id=interconnection_id)
            first = qry.first()
            if first:
                return self._make_interconnection_bgpvpn_assoc_dict(first)

        return None
