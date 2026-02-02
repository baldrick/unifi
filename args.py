FAVOURITE='favourite'
FAVOURITE_GROUP='favourite_group'
IGNORE_GROUP='ignore_group'
LABELS='labels'
PASSED_GROUP='passed_group'
UNIFI_URL='url'
UNIFI_USERNAME='username'
UNIFI_PASSWORD='password'


def get(ctx, name):
    arg = ctx.obj[name]
    if arg is not None:
        if type(arg) is bool:
            return arg
        if len(arg) == 0:
            return None
    return arg
