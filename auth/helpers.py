from django.contrib.auth.models import User  # pylint: disable=E5142


def get_id(user: User):
    if hasattr(user, "oauth"):
        return user.oauth.identification
    return user.username
