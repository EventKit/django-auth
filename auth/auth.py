import logging
import json
import requests

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model

from auth.models import OAuth

logger = logging.getLogger(__name__)


def fetch_user_from_token(access_token):
    """

    :param access_token: Uses OAuth token to retrieve user data from the resource server.
    :return: User object.
    """

    logger.debug('Sending request: access_token="{0}"'.format(access_token))
    try:
        response = requests.get(
            "{0}".format(settings.OAUTH_PROFILE_URL),
            headers={"Authorization": "Bearer {0}".format(access_token)},
        )
        logger.debug("Received response: {0}".format(response.text))
        response.raise_for_status()
    except requests.ConnectionError as err:
        logger.error("Could not reach OAuth Resource Server: {0}".format(err))
        raise OAuthServerUnreachable() from err
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            logger.error(
                "OAuth Resource Server rejected access token: {0}".format(
                    err.response.text
                )
            )
            raise Unauthorized("OAuth Resource Server rejected access token") from err
        logger.error(
            "OAuth Resource Server returned HTTP {0} {1}".format(
                status_code, err.response.text
            )
        )
        raise OAuthError(status_code) from err

    orig_data = response.json()
    logger.debug(f"OAUTH PROFILE DATA: {orig_data}")
    user_data = get_user_data_from_schema(orig_data)

    return get_user(user_data, orig_data)


def clean_data(user_data: dict) -> dict:
    """
    A helper method to remove values that can't be stored in postgres jsonfield
    https://stackoverflow.com/questions/31671634/handling-unicode-sequences-in-postgresql
    :param user_data: A dict
    :return: the dict with "dirty" values removed.
    """
    cleaned_data = {}
    data = user_data or {}
    for field, value in data.items():
        try:
            cleaned_data[field] = value.replace("\u0000", " ")
        except (KeyError, AttributeError):
            logger.debug(f"Unable to encode {field}")
    return cleaned_data


def get_user(user_data, orig_data=None):
    """
    A helper function for retrieving or creating a user given a user_data dictionary.
    :param user_data: A dict containg user data.
    :param orig_data: The original dictionary returned from the OAuth response, not modified to fit our User model.
    :return:
    """
    cleaned_data = clean_data(orig_data)
    try:
        oauth = OAuth.objects.get(identification=user_data.get("identification"))
    except OAuth.DoesNotExist:
        try:
            identification = user_data.pop("identification")
            commonname = user_data.pop("commonname")
        except KeyError as ke:
            logger.error("Required field not provided.")
            raise ke
        try:
            user = get_user_model().objects.create(**user_data)
        except Exception as e:
            # Call authenticate here to log the failed attempt.
            authenticate(username=identification)
            logger.error(
                "The user data provided could not be used to create a user, "
                "it most likely caused by OAUTH_PROFILE_SCHEMA containing an invalid key, or a change "
                "to their identification key."
            )
            logger.error(f"USER DATA: {user_data}")
            raise e
        try:
            OAuth.objects.create(
                user=user,
                identification=identification,
                commonname=commonname,
                user_info=cleaned_data,
            )
        except Exception as e:
            logger.error(
                "The user data provided by the resource server could not be used to create a user, "
                "it most likely caused by OAUTH_PROFILE_SCHEMA mapping is incorrect and/or not providing "
                "a valid identification and commonname."
            )
            logger.error(f"user identification: {identification}")
            logger.error(f"user commonname: {commonname}")
            logger.error(f"user cleaned_data: {cleaned_data}")
            logger.error(f"user orig_data: {orig_data}")
            user.delete()
            raise e
    else:
        if oauth.commonname != user_data.get("commonname"):
            logger.error(
                f"The login commonname ({oauth.commonname}), "
                f"doesn't match the stored commonname ({user_data.get('commonname')})."
            )
            logger.error(
                "This is likely a misconfiguration.  If the information changed it can be updated in the admin console."
            )
            raise Exception("Login Failure: User info does not match.")
        # If logging back in, update their info.
        oauth.user_info = cleaned_data or oauth.user_info
        oauth.save()
        user = oauth.user
    return user


def get_user_data_from_schema(data):
    """
    Uses schema provided in settings to get user_data.
    :param data: user profile data from oauth_service
    :return: a dict of user_data.
    """
    user_data = dict()
    try:
        mapping = json.loads(settings.OAUTH_PROFILE_SCHEMA)
    except AttributeError:
        logger.error(
            "AN OAUTH_PROFILE_SCHEMA was not added to the environment variables."
        )
        raise
    except ValueError:
        raise Error(
            "An invalid json string was added to OAUTH_PROFILE_SCHEMA, please ensure names and values are "
            "quoted properly, that quotes are terminated, and that it is surrounded by braces."
        ) from ValueError
    except TypeError:
        raise Error(
            "AN OAUTH_PROFILE_SCHEMA was added to the environment but it is empty.  Please add a valid "
            "mapping."
        ) from TypeError
    if not mapping:
        raise Error(
            "AN OAUTH_PROFILE_SCHEMA was added to the environment but it an empty json object.  Please add a "
            "valid mapping."
        )
    for key, value_list in mapping.items():
        if not isinstance(value_list, list):
            value_list = [value_list]
        for value in value_list:
            try:
                user_data[key] = data[value]
                break
            except KeyError:
                continue
    return user_data


def request_access_token(auth_code):

    logger.debug('Requesting: code="{0}"'.format(auth_code))
    try:
        response = requests.post(
            settings.OAUTH_TOKEN_URL,
            auth=(settings.OAUTH_CLIENT_ID, settings.OAUTH_CLIENT_SECRET),
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
            },
        )
        logger.debug("Received response: {0}".format(response.text))
        response.raise_for_status()
    except requests.ConnectionError as err:
        logger.error("Could not reach Token Server: {0}".format(err))
        raise OAuthServerUnreachable() from err
    except requests.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 401:
            logger.error(
                "OAuth server rejected user auth code: {0}".format(err.response.text)
            )
            raise Unauthorized("OAuth server rejected auth code") from err
        logger.error(f"OAuth server returned HTTP {err.response.text}",)
        raise OAuthError(status_code) from err
    access = response.json()
    access_token = access.get(settings.OAUTH_TOKEN_KEY)
    if not access_token:
        logger.error(
            "OAuth server response missing `{0}`.  Response Text:\n{1}".format(
                settings.OAUTH_TOKEN_KEY, response.text
            )
        )
        raise InvalidOauthResponse(
            "missing `{0}`".format(settings.OAUTH_TOKEN_KEY), response.text
        )
    return access_token


#
# Errors
#


class Error(Exception):
    """Raise when an error occurs."""


class OAuthServerUnreachable(Error):
    def __init__(self):
        super().__init__("OAuth Server is unreachable")


class OAuthError(Error):
    def __init__(self, status_code):
        super().__init__("OAuth Server responded with HTTP {0}".format(status_code))
        self.status_code = status_code


class InvalidOauthResponse(Error):
    def __init__(self, message, response_text):
        super().__init__("OAuth Server returned invalid response: {0}".format(message))
        self.response_text = response_text


class Unauthorized(Error):
    def __init__(self, message):
        super().__init__("Unauthorized: {0}".format(message))
