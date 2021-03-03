# Django-Auth
Django app for authenticating users

## Setup
To install the Auth app within a Django project, follow the steps below.
1) Run `python setup.py sdist`. This will generate the directory `dist` containing the package `django-auth-<version>.tar.gz`.
2) Run `python -m pip install /dist/django-auth-<version>.tar.gz`. This will make the package available to be installed as an app.
3) Add the app to the Django project's `INSTALLED_APPS`. See [README.rst](README.rst).

## Settings

OAUTH targets specific servers, but it was written to be fairly generic and updating these settings could work out of the box.

| Variable Name | Description |
|---------------|-------------|
|OAUTH_NAME| The name of the Oauth provider (e.g. Google or Facebook) |
|OAUTH_CLIENT_ID| The Oauth ID |
|OAUTH_CLIENT_SECRET| The Oauth Secret |
|OAUTH_AUTHORIZATION_URL| The URL to request the Authorization Code |
|OAUTH_RESPONSE_TYPE| The type of authorization request (default `code`) |
|OAUTH_TOKEN_URL| The URL to request a user token with the Auth Code |
|OAUTH_TOKEN_KEY| The key of the actual token from the OAUTH_TOKEN_URL response. |
|OAUTH_REDIRECT_URI| The URL that the Oauth server should send the user after authorization. |
|OAUTH_DEFAULT_REDIRECT| The default URl to send a user to after login is successful. |
|OAUTH_SCOPE| The level of permission for authorization. |
|OAUTH_PROFILE_URL| The location to request the user profile. |
|OAUTH_PROFILE_SCHEMA| A JSON map of EventKit user schema and the remote user schema. |
The OAUTH PROFILE schema requires several fields
The OAuth profile needs to map to the User model.
The required fields are:
 - identification
 - username
 - commonname

The optional fields are:
 - first_name
 - last_name
 - email

An example:
<pre>
OAUTH_PROFILE_SCHEMA = {"identification": "ID",
                        "username": "username",
                        "email": ["email","mail", "login"],
                        "first_name": "firstname"
                        ...}</pre>
Note an array can be used and EventKit will try each one for a valid value to enter in the EventKit users profile.
