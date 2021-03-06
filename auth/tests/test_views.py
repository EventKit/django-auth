# -*- coding: utf-8 -*-
import logging
import urllib
import base64

from unittest.mock import patch, Mock, MagicMock
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client, override_settings
from django.test import TestCase

from auth.models import OAuth
from auth.views import callback, oauth


logger = logging.getLogger(__name__)


@override_settings(OAUTH_AUTHORIZATION_URL="http://remote.dev/authorize")
class TestAuthViews(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("auth.views.login")
    @patch("auth.views.fetch_user_from_token")
    @patch("auth.views.request_access_token")
    def test_callback(self, mock_get_token, mock_fetch_user, mock_login):
        oauth_name = "provider"
        with self.settings(OAUTH_NAME=oauth_name):
            example_token = "token"

            request = Mock(GET={"code": "1234"})

            user = get_user_model().objects.create(
                username="test", email="test@email.com"
            )
            OAuth.objects.create(
                user=user, identification="test_ident", commonname="test_common"
            )
            mock_get_token.return_value = example_token
            mock_fetch_user.return_value = None
            response = callback(request)
            self.assertEqual(response.status_code, 401)

            mock_login.reset_mock()
            example_state = base64.b64encode("/status/12345".encode())
            request = Mock(GET={"code": "1234", "state": example_state})
            mock_get_token.return_value = example_token
            mock_fetch_user.return_value = user
            response = callback(request)
            mock_login.assert_called_once_with(
                request, user, backend="django.contrib.auth.backends.ModelBackend"
            )
            self.assertRedirects(
                response,
                base64.b64decode(example_state).decode(),
                fetch_redirect_response=False,
            )

    @patch("auth.views.login")
    @patch("auth.views.fetch_user_from_token")
    def test_oauth(self, mock_fetch_user, mock_login):
        # Test GET to ensure a provider name is returned for dynamically naming oauth login.
        oauth_name = "provider"
        client_id = "name"
        redirect_uri = "http://test.dev/callback"
        response_type = "code"
        scope = "profile"
        authorization_url = "http://remote.dev/authorize"
        referer = "/status/12345"

        with self.settings(OAUTH_NAME=oauth_name):
            response = self.client.get(reverse("oauth"), {"query": "name"})
            return_name = response.json().get("name")
            self.assertEqual(return_name, oauth_name)
            self.assertEqual(response.status_code, 200)

        # Test post to ensure that a valid redirect is returned.
        with self.settings(
            OAUTH_CLIENT_ID=client_id,
            OAUTH_REDIRECT_URI=redirect_uri,
            OAUTH_RESPONSE_TYPE=response_type,
            OAUTH_SCOPE=scope,
            OAUTH_NAME=oauth_name,
        ):
            response = self.client.post(reverse("oauth"))
            params = urllib.parse.urlencode(
                (
                    ("client_id", client_id),
                    ("redirect_uri", redirect_uri),
                    ("response_type", response_type),
                    ("scope", scope),
                )
            )
            self.assertRedirects(
                response,
                "{url}?{params}".format(
                    url=authorization_url.rstrip("/"), params=params
                ),
                fetch_redirect_response=False,
            )

            user = get_user_model().objects.create(
                username="test", email="test@email.com"
            )
            OAuth.objects.create(
                user=user, identification="test_ident", commonname="test_common"
            )

            mock_request = MagicMock()
            mock_request.META = {"HTTP_REFERER": referer}
            mock_request.GET = {"query": None}
            mock_request.headers = {}
            response = oauth(mock_request)
            params = urllib.parse.urlencode(
                (
                    ("client_id", client_id),
                    ("redirect_uri", redirect_uri),
                    ("response_type", response_type),
                    ("scope", scope),
                    ("state", base64.b64encode(referer.encode())),
                )
            )
            self.assertRedirects(
                response,
                "{url}?{params}".format(
                    url=authorization_url.rstrip("/"), params=params
                ),
                fetch_redirect_response=False,
            )

            # Test with an Authorization header.
            example_access_token = "1234"
            example_state = base64.b64encode("/status/12345".encode())
            mock_request.GET = {"state": example_state}
            mock_request.headers = {"Authorization": f"Bearer: {example_access_token}"}
            mock_fetch_user.return_value = user
            response = oauth(mock_request)
            mock_fetch_user.assert_called_once_with(example_access_token)
            mock_login.assert_called_once_with(mock_request, user, backend="django.contrib.auth.backends.ModelBackend")

            self.assertRedirects(
                response,
                "/status/12345",
                fetch_redirect_response=False,
            )
