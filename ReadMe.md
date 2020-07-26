# Unifi

[![Gitpod Ready-to-Code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/baldrick/unifi)

## The Scripts

Manage Unifi kit from the command line...

* `deploy-config.sh` - who can ever remember off by heart where `config.gateway.json` (an example of which is supplied) goes?
* `control.sh` - variety of control is possible via the API.
  The main thing I use it for is shutting off my kids from the internet.
  They're on a different WLAN but disabling on WLAN causes all WLANs to disconnect briefly ... which is a pain.  So I now have (un)block/block on a cron on the pi running [pi-hole](https://pi-hole.net/).

## Dependencies
[jq](https://stedolan.github.io/jq/) to parse responses
