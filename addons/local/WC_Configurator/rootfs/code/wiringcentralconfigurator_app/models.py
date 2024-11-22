from django.db import models

# Create your models here.


class LongLivedAccessToken(models.Model):
    token = models.CharField(max_length=200)

    def __str__(self):
        return self.token
