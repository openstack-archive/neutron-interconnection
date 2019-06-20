#!/bin/bash

# Save trace setting
_XTRACE_NEUTRON_INTERCONNECTION=$(set +o | grep xtrace)
set -o xtrace

function neutron_interconnection_configure_role {
    local advsvc_role
    advsvc_role=$(get_or_create_role "advsvc")
    local peer_role
    peer_role=$(get_or_create_role "neutron_interconnection_peer")

    local project
    project=$(get_or_create_project $NEUTRON_INTERCONNECTION_PROJECT "default")

    local user
    user=$(get_or_create_user $NEUTRON_INTERCONNECTION_USERNAME \
        "$NEUTRON_INTERCONNECTION_PASSWORD" "default" "")

    get_or_add_user_project_role $advsvc_role $user $project
    get_or_add_user_project_role $peer_role $user $project
}

function neutron_interconnection_generate_config_files {
    cd $NEUTRON_INTERCONNECTION_DIR && exec ./tools/generate_config_file_samples.sh
}

function neutron_interconnection_configure {
	# Add service plugin to neutron conf
    neutron_service_plugin_class_add interconnection

	# Add conf file
    cp -v $NEUTRON_INTERCONNECTION_DIR/etc/neutron_interconnection.conf.sample $NEUTRON_INTERCONNECTION_CONF
    neutron_server_config_add $NEUTRON_INTERCONNECTION_CONF

    iniset $NEUTRON_INTERCONNECTION_CONF remote_keystone_auth username $NEUTRON_INTERCONNECTION_USERNAME
    iniset $NEUTRON_INTERCONNECTION_CONF remote_keystone_auth password $NEUTRON_INTERCONNECTION_PASSWORD
    iniset $NEUTRON_INTERCONNECTION_CONF remote_keystone_auth project $NEUTRON_INTERCONNECTION_PROJECT
    inicomment $NEUTRON_INTERCONNECTION_CONF drivers network_l2_driver
    iniadd $NEUTRON_INTERCONNECTION_CONF drivers network_l2_driver $NEUTRON_INTERCONNECTION_NETWORK_L2_DRIVER
    inicomment $NEUTRON_INTERCONNECTION_CONF drivers network_l3_driver
    iniadd $NEUTRON_INTERCONNECTION_CONF drivers network_l3_driver $NEUTRON_INTERCONNECTION_NETWORK_L3_DRIVER
    inicomment $NEUTRON_INTERCONNECTION_CONF drivers router_driver
    iniadd $NEUTRON_INTERCONNECTION_CONF drivers router_driver $NEUTRON_INTERCONNECTION_ROUTER_DRIVER
}

if [[ "$1" == "stack" && "$2" == "install" ]]; then
    echo_summary "Installing neutron-interconnection"
    setup_develop $NEUTRON_INTERCONNECTION_DIR
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    echo_summary "Configuring neutron-interconnection"
    neutron_interconnection_configure_role
    neutron_interconnection_generate_config_files
    neutron_interconnection_configure
fi

# Restore trace setting
${_XTRACE_NEUTRON_INTERCONNECTION}
