import json
import logging
from talk.api import TalkAPI

logger = logging.getLogger(__name__)


def get_contacts(ctx):
    # TODO: add filtering by labels (= contact list).
    api = TalkAPI(ctx)
    contacts = api.get_contacts()
    if contacts is None:
        logger.info('no contacts found')
        return
    labels = ctx.obj['labels']
    if len(labels) > 0:
        cl_map = api.get_contact_lists()
        contacts = [c for c in contacts if intersects(cl_map, c.get('contact_lists'), labels)]
    logger.info(json.dumps(contacts, indent=2))
    logger.info(f'{len(contacts)} contacts found')


def get_contact_lists(ctx):
    api = TalkAPI(ctx)
    contact_lists = api.get_contact_lists()
    logger.info(f'{len(contact_lists)} contact lists found: {json.dumps(contact_lists, indent=2)}')


def intersects(cl_map, cl_ids, labels):
    set_ids = set(cl_ids)
    set_label_ids = set(cl_map[l].get('id', '') for l in labels)
    return len(set_ids.intersection(set_label_ids)) > 0