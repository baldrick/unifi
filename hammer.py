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
def cli(ctx, favourite, label, loglevel):
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s %(message)s', datefmt='%H:%M:%S', level=getattr(logging, loglevel.upper(), None))
    ctx.ensure_object(dict)
    ctx.obj['favourite'] = favourite
    ctx.obj['labels'] = label
    ctx.obj['loglevel'] = loglevel.upper()

'''
unifi command group.
'''
@cli.group()
@click.option('--url', envvar='UNIFI_URL', help='Unifi server address')
@click.option('--username', envvar='UNIFI_USERNAME', help='Unifi username')
@click.option('--password', envvar='UNIFI_PASSWORD', help='Unifi password')
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
@click.option('--additive', is_flag=True, default=False, help='only used with --unifi_talk, does not delete existing contacts or contact lists so use with care')
@click.option('--concatenate', help='combine contacts into a single file / contact list with the given name')
@click.option('--output', multiple=True, type=click.Choice(['grandstream.xml', 'unifi.csv', 'unifi.talk']), help='the output(s) required  ')
@click.pass_context
def sync(ctx, additive, concatenate, output):
    talk.sync.sync_contacts(ctx, additive, concatenate, output)

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