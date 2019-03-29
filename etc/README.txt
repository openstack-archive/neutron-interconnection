To generate the sample neutron-interconnection configuration files and
the sample policy file, run the following commands respectively
from the top level of the neutron-interconnection directory:

  tox -e genconfig
  tox -e genpolicy

If a 'tox' environment is unavailable, then you can run
the following commands respectively
instead to generate the configuration files:

  oslo-config-generator --config-file etc/oslo-config-generator/neutron-interconnection.conf
  oslopolicy-sample-generator --config-file=etc/oslo-policy-generator/policy.conf