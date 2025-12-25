from django.db import models


class PlaceCoordinates(models.Model):
    address = models.CharField(max_length=255, unique=True)
    lat = models.FloatField()
    lon = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.address
