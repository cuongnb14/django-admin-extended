from django.db import models


class Bookmark(models.Model):
    name = models.CharField(max_length=45)
    url = models.CharField(max_length=1000)
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name
