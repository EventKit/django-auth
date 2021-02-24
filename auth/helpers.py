from datetime import datetime
import pytz

from django.contrib.auth.models import User  # pylint: disable=E5142
from django.conf import settings


def get_id(user: User):
    if hasattr(user, "oauth"):
        return user.oauth.identification
    return user.username


def set_session_user_last_active_at(request):
    # Set last active time, which is used for auto logout.
    last_active_at = datetime.utcnow().replace(tzinfo=pytz.utc)
    request.session[settings.SESSION_USER_LAST_ACTIVE_AT] = last_active_at.isoformat()

    # Return the last active datetime for convenience.
    return last_active_at
