2. Edit the ``/etc/neutron_interconnection/neutron_interconnection.conf`` file and complete the following
   actions:

   * In the ``[database]`` section, configure database access:

     .. code-block:: ini

        [database]
        ...
        connection = mysql+pymysql://neutron_interconnection:NEUTRON_INTERCONNECTION_DBPASS@controller/neutron_interconnection
