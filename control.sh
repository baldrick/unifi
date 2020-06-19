#!/bin/bash

# Inspired by https://gist.github.com/jcconnell/0ee6c9d5b25c572863e8ffa0a144e54b
# API documented here: https://ubntwiki.com/products/software/unifi-controller/api

function usage() {
     cat << END_USAGE
     Usage: $0 -u <username> -p <password> -c <dump|disable|enable|status|block|unblock|force-provision> -w <wifi-name> -C <client name>
         -u: ${unifi_username}
         -p: ${unifi_password}
         -c: ${cmd} chosen from available commands:
            dump wifi networks
            disable/enable a wifi netork
            status check a wifi network
            block/unblock a client
            force-provision a device
         -w: ${wifi_name} (required for disable/enable/status)
         -C: ${client_names} (required for block/unblock/force-provision, comma separated list of client names/devices)
END_USAGE
    exit -1
}

function init() {
    unifi_controller=https://unifi.home:8443
    unifi_site_url="${unifi_controller}/api/s/default"
    cookie=/tmp/cookie
    curl_cmd="curl --silent --show-error --cookie ${cookie} --cookie-jar ${cookie} --insecure "

    process_arguments "$@"
    exit_if_invalid_arguments
}

function process_arguments() {
    while getopts "u:p:c:w:C:" arg; do
        case $arg in
            u) unifi_username="$OPTARG";;
            p) unifi_password="$OPTARG";;
            c) cmd="$OPTARG";;
            w) wifi_name="$OPTARG";;
            C) client_names="$OPTARG";;
            *) usage;;
        esac
    done
}

function exit_if_invalid_arguments() {
    if [[ -z ${unifi_username} ]] || [[ -z ${unifi_password} ]] || [[ -z ${cmd} ]]
    then
        usage
    fi

    case ${cmd} in
        block|unblock|force-provision)
            if [[ -z ${client_names} ]]
            then
                usage
            fi
            ;;
        disable|enable|status)
            if [[ -z ${wifi_name} ]]
            then
                usage
            fi
            ;;
        *) ;;
    esac
}

function unifi_login() {
    local l_data="{\"password\":\"$unifi_password\",\"username\":\"$unifi_username\"}"
    ${curl_cmd}                                     \
        --header "Content-Type: application/json"   \
        --request POST                              \
        --data ${l_data}                            \
        ${unifi_controller}/api/login               \
        > /dev/null
}

function unifi_logout() {
    ${curl_cmd} $unifi_controller/logout
    rm ${cookie}
}

function get() {
    local l_resource=$1
    ${curl_cmd}                                 \
        "${unifi_site_url}/rest/${l_resource}"  \
        --compressed
}

function put() {
    local l_endpoint="$1"
    local l_data="$2"
    ${curl_cmd}                                 \
        "${unifi_site_url}/rest/${l_endpoint}"  \
        --compressed                            \
        --request PUT                           \
        --data-binary "${l_data}"               \
        > /dev/null
}

function post_command() {
    local l_manager=$1
    local l_cmd=$2
    local l_data="$3"
    local l_json="{\"cmd\": \"${l_cmd}\""
    if [ ! -z "${l_data}" ]
    then
        l_json="${l_json},${l_data}"
    fi
    l_json="${l_json}}"
    local l_response=$(                             \
        ${curl_cmd}                                 \
            "${unifi_site_url}/cmd/${l_manager}"    \
            --compressed                            \
            --request POST                          \
            --data "${l_json}"                      \
        )
    echo ${l_response} | jq
}

function get_wifi_id_from_name() {
    local l_wifi_name="$1"
    local l_response=$(get wlanconf)
    local l_wlans=$(echo ${l_response} | jq ".data[] | {id: ._id, name: .name}")
    echo ${l_wlans} | jq "if .name == \"${l_wifi_name}\" then .id else null end" | grep \" | tr -d '"'
}

function dump_wlans() {
    local l_response=$(get wlanconf)
    echo ${l_response} | jq --compact-output ".data[] | {name: .name, enabled: .enabled}"
}

function disable_wifi() {
    local l_wifi_name="$1"
    echo "Disabling ${l_wifi_name}"
    local l_wifi_id=$(get_wifi_id_from_name "${l_wifi_name}")
    put wlanconf/${l_wifi_id} '{"_id":"'"$site_id"'","enabled":false}'
    #${curl_cmd} "$unifi_controller"'/api/s/default/rest/wlanconf/'"$l_wifi_id" -X PUT --data-binary '{"_id":"'"$site_id"'","enabled":false}' --compressed > /dev/null
}

function enable_wifi() {
    local l_wifi_name="$1"
    echo "Enabling ${l_wifi_name}"
    local l_wifi_id=$(get_wifi_id_from_name "${l_wifi_name}")
    put wlanconf/${l_wifi_id} '{"_id":"'"$site_id"'","enabled":true}'
    #${curl_cmd} "$unifi_controller"'/api/s/default/rest/wlanconf/'"$l_wifi_id" -X PUT --data-binary '{"_id":"'"$site_id"'","enabled":true}' --compressed > /dev/null
}

function check_status() {
    local l_wifi_name="$1"
    local l_wifi_id=$(get_wifi_id_from_name "${l_wifi_name}")
    echo -n "${l_wifi_name} (${l_wifi_id}) is "
    local l_response=$(get wlanconf/${l_wifi_id})
    local l_status=$(echo ${l_response} | jq ".data[0].enabled")
    if [ "${l_status}" == "true" ]; then
        echo "up"
    elif [ "${l_status}" == "false" ]; then
        echo "down"
    else
        echo "unknown (response: ${l_response})"
    fi
}

function get_mac() {
    local l_client_name="$@"
    local l_response=$(get user)
    local l_clients=$(echo ${l_response} | jq ".data[] | {mac: .mac, name: .name}")
    echo ${l_clients} | jq "if .name == \"${l_client_name}\" then .mac else null end" | grep \" | tr -d '"'
}

function json_mac() {
    local l_mac=$1
    echo "\"mac\": \"${l_mac}\""
}

function manage_clients() {
    local l_cmd=$1
    local l_client_names="$2"

    while read l_client_name
    do
        echo "Doing ${l_client_name}"
        local l_mac=$(get_mac "${l_client_name}")
        post_command stamgr ${l_cmd} "$(json_mac "${l_mac}")"
    done < <(echo "${l_client_names}" | tr ',' '\n')
}

function block_clients() {
    local l_client_names="$1"
    manage_clients block-sta "${l_client_names}"
}

function unblock_clients() {
    local l_client_names="$1"
    manage_clients unblock-sta "${l_client_names}"
}

function force_provision() {
    local l_device_name=$1
    local l_mac=$(get_mac "${l_device_name}")
    post_command devmgr force-provision "$(json_mac "${l_mac}")"
}

function execute() {
    unifi_login
    case "$cmd" in
        "block")
            block_clients "${client_names}"
            ;;
        "disable")
            disable_wifi "${wifi_name}"
            ;;
        "dump")
            dump_wlans
            ;;
        "enable")
            enable_wifi "${wifi_name}"
            ;;
        "force-provision")
            force_provision "${client_names}"
            ;;
        "status")
            check_status "${wifi_name}"
            ;;
        "unblock")
            unblock_clients "${client_names}"
            ;;
        *)
            usage
            ;;
    esac
    unifi_logout
}

init "$@"
execute
