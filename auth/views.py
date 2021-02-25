# -*- coding: utf-8 -*-

from logging import getLogger
import base64
from urllib.parse import urlencode
import requests

from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import redirect

from auth.auth import request_access_token, fetch_user_from_token
from auth.helpers import get_id

logger = getLogger(__name__)


def oauth(request):
    """
    :return: A redirection to the OAuth server (OAUTH_AUTHORIZATION_URL) provided in the settings
    """
    if not getattr(settings, "OAUTH_AUTHORIZATION_URL", None):
        logger.error("OAUTH_AUTHORIZATION_URL is not set.")
        return JsonResponse(
            {"error": "Server error. Contact an administrator."}, status=500
        )

    if request.GET.get("query"):
        return JsonResponse({"name": settings.OAUTH_NAME}, status=200,)

    params = [
        ("client_id", settings.OAUTH_CLIENT_ID),
        ("redirect_uri", settings.OAUTH_REDIRECT_URI),
        ("response_type", settings.OAUTH_RESPONSE_TYPE),
        ("scope", settings.OAUTH_SCOPE),
    ]

    if request.META.get("HTTP_REFERER"):
        params += [
            ("state", base64.b64encode(request.META.get("HTTP_REFERER").encode()),)
        ]
    encoded_params = urlencode(params)

    return redirect(
        "{0}?{1}".format(settings.OAUTH_AUTHORIZATION_URL.rstrip("/"), encoded_params)
    )


def callback(request):
    try:
        access_token = request_access_token(request.GET.get("code"))
        user = fetch_user_from_token(access_token)
        state = request.GET.get("state")
        if user:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            logger.info('User "{0}" has logged in successfully'.format(get_id(user)))
            if state:
                return redirect(base64.b64decode(state).decode())
            return redirect("dashboard")
        logger.error("User could not be logged in.")
        return JsonResponse({"error": "User could not be logged in"}, status=401,)
    except (
        requests.exceptions.RequestException,
        AttributeError,
        ValueError,
        TypeError,
    ) as e:
        # Unless otherwise noted, we want any exception to redirect to the error page.
        logger.error("Exception occurred during oauth, redirecting user.")
        logger.error(e)
        if getattr(settings, "DEBUG"):
            raise
        return JsonResponse({"error": "User could not be logged in"}, status=500,)
