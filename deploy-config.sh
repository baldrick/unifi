#!/bin/bash

scp config.gateway.json uck:/srv/unifi/data/sites/default

./control.sh -u ${UNIFI_USERNAME} -p ${UNIFI_PASSWORD} -c force-provision -C usg
