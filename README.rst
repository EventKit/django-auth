=====
Auth
=====

Auth is a Django app used to enable user authentication.


Quick start
-----------

1. Add "auth" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        "auth.apps.AuthConfig",
    ]

2. Include the auth URLconf in your project urls.py like this::

    path('auth/', include('auth.urls')),


