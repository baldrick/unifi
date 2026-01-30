# Unifi CLI

This is a Python-based CLI to interact with Unifi kit.  If you've got constructive criticism about my Python code please let me know - I haven't written a lot of it ;-)

Important: as it stands, the interactions with any Unifi controller are insecure.  If you're the subject of a man-in-the-middle attack, that's on you.

So far this is just aimed at syncing Google contacts with Unifi Talk.  You need to set up your own Google project with access to the people API if you want to do this.  Currently you must set up contact lists in Unifi with the same names as the labels of Google contacts you wish to import, this sync won't do that for you (yet).

Note: Unifi Talk endpoints used here have been reverse-engineered so may break if Unifi change their API (it's not documented).

There's a hierarchy of commands to simplify adding network / protect at some point.  `talk` is the only top level command at the moment.

All commands expect these flags:

* `--server` is the endpoint of your Unifi controller
* `--username` is the name of the user to log in to the controller
* `--password` is, well, duh, the password of the user

And there's an optional flag:

* `--log-level` to control, obvs, log level (DEBUG, INFO, etc.)

To run the CLI you'll first need to:

* create a new python environment, e.g. `python -m venv yourenv`
* activate that environment with `source yourenv/bin/activate`
* `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
* (optional) Switch interpreter to the env-specific one if you're going to edit in VS-Code
  *  I assume there are similar switches with other IDEs, you'll need to figure that out yourself.
* Run `deactivate` when you're done & want to leave the environment.

## Talk

`talk` supports the following command structure:

* get - to get contact info
  * contacts - get contact info
  * lists - get contact lists
* sync - synchronize Google contacts with Unifi Talk; *deletes all existing Unifi Talk contacts!*
  * takes a list of `labels` - these correspond to labels in Google contacts.  Be careful of importing labels where one contact appears in both, de-duplication at that level is not handled.
  * If the `--csv` argument is given, a CSV file per label will be written in Unifi-compliant form ready for importing.
  * If the `--unifi` argument is given, the contacts will be directly uploaded to Unifi Talk and associated with a contact list of the same name as the label.

For example:

```shell
$ python unifi.py --server https://your.unifi --username you --password yourpwd talk get contacts
# outputs raw contact info

$ python unifi.py --server https://your.unifi --username you --password yourpwd talk get lists
# outputs raw contact lists

$ ./unifi.py --server https://your.unifi --username you --password yourpwd sync --labels Family Friends --csv --unifi
# Gets contacts from Google labelled "Family" or "Friends".
# Writes two files: Family.csv and Friends.csv
# Then deletes *all* contacts from Unifi Talk,
# replaces them with the ones downloaded from Google
# and associates the downloaded contacts with the contact list of the same name.
```

### Caveats

Unifi Talk's contact management is ... limited.

e.g. a phone number can't be used by more than one contact (presumably so reverse lookup can do something sensible to tell you who's calling).  This is a pain if people live together and you have their landline number (perhaps anachronistic in the modern age of people only having mobies and eschewing landlines but in my case plenty of people still have one) against both contacts.  I've attempted to address this by creating a "<surname> home (<first names>)" contact and removing the home phone number from other contacts.  It works for me.

You're also limited to home, work & mobile numbers (ok and fax (!) and _other_, both of which I've ignored) so your Google contacts need to have phone numbers with these details.  If there's no phone number against a Google contact, it won't get imported (what would be the point?).