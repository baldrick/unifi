import json
import logging
from talk.api import TalkAPI

logger = logging.getLogger(__name__)


def get_contacts(ctx):
    api = TalkAPI(ctx)
    contacts = api.get_contacts()
    if contacts is not None:
        logger.info(f'{len(contacts)} contacts found: {json.dumps(contacts, indent=2)}')


def get_contact_lists(ctx):
    api = TalkAPI(ctx)
    contact_lists = api.get_contact_lists()
    logger.info(f'{len(contact_lists)} contact lists found: {json.dumps(contact_lists, indent=2)}')
