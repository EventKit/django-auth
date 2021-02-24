from django.contrib.auth import get_user_model
from django.db.models import JSONField
from django.db import models


class OAuth(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, blank=False)
    identification = models.CharField(max_length=200, unique=True, blank=False)
    commonname = models.CharField(max_length=100, blank=False)
    user_info = JSONField(default=dict)

    class Meta:  # pragma: no cover
        managed = True
        db_table = "auth_oauth"

    def __str__(self):
        return "{0}".format(self.commonname)
