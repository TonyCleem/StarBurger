from django.db import models


class PlaceCoordinates(models.Model):
    address = models.CharField(
        max_length=255, unique=True, verbose_name="кэшированный адрес"
    )
    lat = models.FloatField(blank=True, verbose_name="широта")
    lon = models.FloatField(blank=True, verbose_name="долгота")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="дата обновления")

    def __str__(self):
        return self.address
