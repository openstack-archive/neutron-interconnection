============================
neutron-interconnection.conf
============================

To use ``neutron-interconnection`` service, you need to configure the following
parameters:

* specific user remote Keystone credentials (username, password and project)
  in ``[remote_keystone_auth]`` group of the neutron server,
* interconnection mechanism drivers for network L2, L3 and/or router connectivity
  in ``[drivers]`` group of the neutron server.

.. show-options::
   :config-file: etc/oslo-config-generator/neutron-interconnection.conf
