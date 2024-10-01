from django.db import models

# Create your models here.

# Model to store received POST requests
class ReceivedRequest(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    strat_name = models.CharField(max_length=255, null=True, blank=True)
    alert = models.CharField(max_length=255, null=True, blank=True)
    exchange = models.CharField(max_length=255, null=True, blank=True)
    symbol = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    direction = models.CharField(max_length=10, null=True, blank=True)
    tradeReqId = models.IntegerField(null=True, blank=True)  # New field to store trade request ID

    def __str__(self):
        return f"{self.timestamp} - {self.symbol} ({self.direction})"