import click
import logging
import google_contacts
import talk.get
import talk.sync

logger = logging.getLogger(__name__)


'''
Top level CLI command with options that may apply to every command.
'''
@click.group()
@click.option('--favourite', is_flag=True, default=False, help='only use favourite (starred) contacts')
@click.option('--label', multiple=True, help='apply functions only to the given label(s)')
@click.option('--loglevel', default='INFO', help='set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
@click.pass_context
def cli(ctx, favourite, loglevel, label):
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s %(message)s', datefmt='%H:%M:%S', level=getattr(logging, loglevel.upper(), None))
    ctx.ensure_object(dict)
    ctx.obj['favourite'] = favourite
    ctx.obj['loglevel'] = loglevel.upper()
    ctx.obj['labels'] = label

'''
unifi command group.
'''
@cli.group()
@click.option('--url', help='Unifi server address')
@click.option('--username', help='Unifi username')
@click.option('--password', help='Unifi password')
@click.pass_context
def unifi(ctx, url, username, password):
    ctx.obj['url'] = url
    ctx.obj['username'] = username
    ctx.obj['password'] = password

'''
unifi talk command group.
'''
@unifi.group('talk')
@click.pass_context
def talk_cli(ctx):
    pass

'''
unifi talk get command group.
'''
@talk_cli.group()
@click.pass_context
def get(ctx):
    pass

'''
unifi talk get contacts.
'''
@get.command(help='retrieve contacts')
@click.pass_context
def contacts(ctx):
    talk.get.get_contacts(ctx)

'''
unifi talk get lists
'''
@get.command(help='retrieve contact lists')
@click.pass_context
def lists(ctx):
    talk.get.get_contact_lists(ctx)

'''
unifi talk sync command
'''
@talk_cli.command()
@click.option('--concatenate', help='combine contacts into a single file / contact list with the given name')
@click.option('--grandstream', is_flag=True, default=False, help='output contacts to XML file for Grandstream')
@click.option('--unifi_csv', is_flag=True, default=False, help='output contacts (without contact list association) to CSV file for Unifi Talk')
@click.option('--unifi_talk', is_flag=True, default=False, help='one-way sync contacts with Unifi Talk')
@click.pass_context
def sync(ctx, concatenate, grandstream, unifi_csv, unifi_talk):
    talk.sync.sync_contacts(ctx, concatenate, grandstream, unifi_csv, unifi_talk)

'''
google command group.
'''
@cli.group()
@click.pass_context
def google(ctx):
    pass

'''
google get
'''
@google.command()
@click.pass_context
@click.option('--raw', is_flag=True, default=False, help='output raw fetch results')
@click.option('--parsed', is_flag=True, default=False, help='output parsed fetch results')
def get(ctx, raw, parsed):
    google_contacts.get(ctx, raw, parsed)

if __name__ == "__main__":
    cli(obj={})