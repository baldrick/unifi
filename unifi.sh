function login() {
    [[ -d .unifi ]] || mkdir .unifi
    if [[ -f .unifi/cookie.txt ]] then
        echo "$COOKIE already exists, assuming logged in"
        CSRF_TOKEN=$(cat .unifi/xcsrf)
        export XCSRF="X-CSRF-Token: $CSRF_TOKEN"
        return
    fi
    if [[ -f .pwd ]] then
        UNIFI_PASSWORD=$(cat .pwd)
    else
        echo ".pwd file not found, prompting for password"
        read -s -p "Enter Unifi password: " UNIFI_PASSWORD
    fi
    REQUEST_PATH="/api/auth/login"
    DATA="{\"username\":\"baldrick\",\"password\":\"$UNIFI_PASSWORD\"}"
    echo $DATA
    CURL_OUTPUT=$(curl -i --insecure --cookie-jar "$COOKIE" -H "$JSON_CONTENT" --data "$DATA" ${UNIFI}${REQUEST_PATH})
    echo "--- curl output ---- ($?)"
    echo "$CURL_OUTPUT"
    echo "--------------------"
    if [[ ! "$CURL_OUTPUT" =~ "HTTP/2 200" ]] then
        echo "Login failed"
        rm -r "$COOKIE"
        exit 1
    fi
    CSRF_TOKEN=$(echo "$CURL_OUTPUT" | grep -i '^x-csrf-token:' | awk '{print $2}')
    echo $CSRF_TOKEN > .unifi/xcsrf
    export XCSRF="X-CSRF-Token: $CSRF_TOKEN"
}

function get_contacts() {
    # Get contacts from Unifi Talk.
    REQUEST_PATH="/proxy/talk/api/contacts"
    echo curl --insecure --cookie "$COOKIE" -H "$XCSRF" ${UNIFI}${REQUEST_PATH}
    curl --insecure --cookie "$COOKIE" -H "$XCSRF" ${UNIFI}${REQUEST_PATH}
}

function get_contact_lists() {
    # Get contacts lists.
    REQUEST_PATH="/proxy/talk/api/contact_list"
    curl --insecure --cookie "$COOKIE" -H "$XCSRF" ${UNIFI}${REQUEST_PATH}
}

function add_contact_to_list() {
    # Put contacts into a specific contacts list.
    CONTACT_LIST_ID=2 # Family
    REQUEST_PATH="/proxy/talk/api/contact_list/${CONTACT_LIST_ID}"
    DATA='{"contacts":[70,74,88,87],"name":"Family"}'
    curl --insecure --cookie "$COOKIE" -H "$XCSRF" -H "$JSON_CONTENT" -X PUT -d "$DATA" ${UNIFI}${REQUEST_PATH}
}

function add_contacts_to_lists() {
    # Put contacts into a set of contacts lists.
    REQUEST_PATH="/proxy/talk/api/contact_list/batch_assign"
    DATA='{"contactIds":[87],"listIds":[2]}'
    curl --insecure --cookie "$COOKIE" -H "$XCSRF" -H "$JSON_CONTENT" -X POST -d "$DATA" ${UNIFI}${REQUEST_PATH}
}

UNIFI="https://192.168.1.2"
JSON_CONTENT="Content-Type: application/json"
COOKIE=".unifi/cookie.txt"
PYTHON=contacts-sync/bin/python

# TODO:
# - for batch assign, look up existing contacts in list, add new ones, and PUT the full list back.
# - add "delete contact list" method, call this when syncing contacts.

case $1 in
  "login")
    shift
    login $@
    ;;
  "logout")
    rm -r .unifi
    echo "Logged out"
    ;;
  "get-contacts")
    shift
    login $@
    get_contacts
    ;;
  "get-contact-lists")
    shift
    login $@
    get_contact_lists
    ;;
  "clear")
    shift
    login $@
    DATA='{"ids":["d7e12964-bd18-4d76-bc3a-668d4676d161"]}'
    curl --insecure --cookie "$COOKIE" -H "$XCSRF" -H "$JSON_CONTENT" -X POST -d "$DATA" ${UNIFI}/proxy/talk/api/contact/delete
    ;;
  "sync-contacts")
    $PYTHON ~/dev/contact-sync/get_contacts.py --labels Family Friends
    # TODO:
    # - find contact lists, one per label ... if they don't exist, exit/create?
    # - delete contacts in Talk
    # - upload contacts from CSVs
    # - assign contacts to lists
    ;;
  *)
    echo "Usage: unifi.sh {get-contacts|upload-contacts}"
    ;;
esac