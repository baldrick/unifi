# Unifi CLI

Python-based CLI to interact with Unifi kit.

Important: as it stands the interactions with any Unifi controller are insecure.  If you're the subject of a man-in-the-middle attack, that's on you.

So far just used to sync Google contacts with Unifi Talk.  You need to set up your own Google project with access to the people API if you want to do this.

Calls to Unifi Talk are reverse-engineered so may break if Unifi change their API (it's not documented).

There's a hierarchy of commands to simplify adding network / protect at some point.  `talk` is the only top level command at the moment.

All commands expect these flags:

* `--server` is the endpoint of your Unifi controller
* `--username` is the name of the user to log in to the controller
* `--password` is, well, duh, the password of the user

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
* sync - synchronize Google contacts with Unifi Talk; deletes all existing Unifi Talk contacts!
  * takes a list of `labels` - these correspond to labels in Google contacts.  Be careful of importing labels where one contact appears in both, de-duplication at that level is not handled.

For example:

```shell
$ python unifi.py --server https://your.unifi --username you --password yourpwd talk get contacts
# outputs raw contact info

$ python unifi.py --server https://your.unifi --username you --password yourpwd talk get lists
# outputs raw contact lists
```

### Caveats

Unifi Talk's contact management is ... limited.

e.g. a phone number can't be used by more than one contact (presumably so reverse lookup can do something sensible to tell you who's calling).  This is a pain if people live together and you have their landline number (perhaps anachronistic in the modern age of people only having mobies and eschewing landlines but in my case plenty of people still have one) against both contacts.  I've attempted to address this by creating a "<surname> home (<first names>)" contact and removing the home phone number from other contacts.  It works for me.

You're also limited to home, work & mobile numbers (ok and fax (!) and _other_ both of which I've ignored) so your Google contacts need to have phone numbers with these details.  If there's no phone number against a Google contact, it won't get imported (what would be the point?).