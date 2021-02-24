import logging

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

from auth.models import OAuth

logger = logging.getLogger(__name__)


class OAuthAdmin(admin.ModelAdmin):

    search_fields = ["user__username", "identification", "commonname", "user_info"]
    list_display = ["user", "identification", "commonname"]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions


class OAuthInline(admin.StackedInline):
    model = OAuth


class CustomUserAdmin(UserAdmin):

    inlines = [OAuthInline]

    readonly_fields = UserAdmin.readonly_fields + ("last_login", "date_joined",)


admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), CustomUserAdmin)
admin.site.register(OAuth, OAuthAdmin)
