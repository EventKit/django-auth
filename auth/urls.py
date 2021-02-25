# -*- coding: utf-8 -*-


from django.urls import re_path
from django.views.decorators.csrf import ensure_csrf_cookie

from auth.views import oauth, callback

urlpatterns = [
    re_path(r"^oauth$", ensure_csrf_cookie(oauth), name="oauth"),
    re_path(r"^callback$", ensure_csrf_cookie(callback), name="callback"),
]
