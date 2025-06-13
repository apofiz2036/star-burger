from django.db import models


class AddressCoordinates(models.Model):
    address = models.CharField(max_length=300, unique=True, verbose_name='Адрес')
    lat = models.FloatField(null=True, blank=True, verbose_name='Широта')
    lon = models.FloatField(null=True, blank=True, verbose_name='Долгота')
    updated_at = models.DateField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Координаты адреса'
        verbose_name_plural = 'Координаты адресов'

    def __str__(self):
        return f'{self.address} ({self.lat}, {self.lon})'
