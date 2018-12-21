Prerequisites
-------------

Before you install and configure the neutron-interconnection service,
you must create a database, service credentials, and API endpoints.

#. To create the database, complete these steps:

   * Use the database access client to connect to the database
     server as the ``root`` user:

     .. code-block:: console

        $ mysql -u root -p

   * Create the ``neutron_interconnection`` database:

     .. code-block:: none

        CREATE DATABASE neutron_interconnection;

   * Grant proper access to the ``neutron_interconnection`` database:

     .. code-block:: none

        GRANT ALL PRIVILEGES ON neutron_interconnection.* TO 'neutron_interconnection'@'localhost' \
          IDENTIFIED BY 'NEUTRON_INTERCONNECTION_DBPASS';
        GRANT ALL PRIVILEGES ON neutron_interconnection.* TO 'neutron_interconnection'@'%' \
          IDENTIFIED BY 'NEUTRON_INTERCONNECTION_DBPASS';

     Replace ``NEUTRON_INTERCONNECTION_DBPASS`` with a suitable password.

   * Exit the database access client.

     .. code-block:: none

        exit;

#. Source the ``admin`` credentials to gain access to
   admin-only CLI commands:

   .. code-block:: console

      $ . admin-openrc

#. To create the service credentials, complete these steps:

   * Create the ``neutron_interconnection`` user:

     .. code-block:: console

        $ openstack user create --domain default --password-prompt neutron_interconnection

   * Add the ``admin`` role to the ``neutron_interconnection`` user:

     .. code-block:: console

        $ openstack role add --project service --user neutron_interconnection admin

   * Create the neutron_interconnection service entities:

     .. code-block:: console

        $ openstack service create --name neutron_interconnection --description "neutron-interconnection" neutron-interconnection

#. Create the neutron-interconnection service API endpoints:

   .. code-block:: console

      $ openstack endpoint create --region RegionOne \
        neutron-interconnection public http://controller:XXXX/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        neutron-interconnection internal http://controller:XXXX/vY/%\(tenant_id\)s
      $ openstack endpoint create --region RegionOne \
        neutron-interconnection admin http://controller:XXXX/vY/%\(tenant_id\)s
