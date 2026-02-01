import click
import logging
import google_contacts.google_contacts
import talk.get.get
import talk.sync.sync

@click.group()
@click.option('--loglevel', help='set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)', default='INFO')
@click.option('--label', multiple=True, help='apply functions only to the given label(s)')
@click.pass_context
def cli(ctx, loglevel, label):
    ctx.ensure_object(dict)
    ctx.obj['loglevel'] = loglevel
    ctx.obj['labels'] = label
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s %(message)s', datefmt='%H:%M:%S', level=getattr(logging, loglevel.upper(), None))


@cli.group()
@click.option('--url', help='Unifi server address')
@click.option('--username', help='Unifi username')
@click.option('--password', help='Unifi password')
@click.pass_context
def unifi(ctx, url, username, password):
    ctx.obj['url'] = url
    ctx.obj['username'] = username
    ctx.obj['password'] = password

@unifi.group('talk')
@click.pass_context
def talk_cli(ctx):
    pass

@talk_cli.group()
@click.pass_context
def get(ctx):
    pass

@talk_cli.command()
@click.option('--grandstream', is_flag=True, default=False, help='output contacts to XML file for Grandstream')
@click.option('--unifi_csv', is_flag=True, default=False, help='output contacts to CSV file for Unifi Talk')
@click.option('--unifi_talk', is_flag=True, default=False, help='one-way sync contacts with Unifi Talk')
@click.pass_context
def sync(ctx, grandstream, unifi_csv, unifi_talk):
    talk.sync.sync.sync_contacts(ctx, grandstream, unifi_csv, unifi_talk)

@get.command(help='retrieve contacts')
@click.pass_context
def contacts(ctx):
    talk.get.get.get_contacts(ctx)

@get.command(help='retrieve contact lists')
@click.pass_context
def lists(ctx):
    talk.get.get.get_contact_lists(ctx)

@cli.group()
@click.pass_context
def google(ctx):
    pass

@google.command()
@click.pass_context
@click.option('--raw', is_flag=True, default=False, help='output raw fetch results')
@click.option('--parsed', is_flag=True, default=False, help='output parsed fetch results')
def get(ctx, raw, parsed):
    google_contacts.google_contacts.get(ctx, raw, parsed)

if __name__ == "__main__":
    cli(obj={})