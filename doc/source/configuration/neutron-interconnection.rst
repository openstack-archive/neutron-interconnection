============================
neutron-interconnection.conf
============================

To use neutron-interconnection, you need to configure remote Keystone credentials
(username, password and project) of ``neutron-interconnection`` service specific
user in ``[remote_keystone_auth]`` group of the neutron server.

.. show-options::
   :config-file: etc/oslo-config-generator/neutron-interconnection.conf
