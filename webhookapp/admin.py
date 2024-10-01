from django.contrib import admin
from .models import ReceivedRequest

# Register your models here.
@admin.register(ReceivedRequest)
class ReceivedRequestAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'strat_name', 'symbol', 'price', 'direction', 'alert', 'exchange')
    search_fields = ('symbol', 'strat_name', 'exchange')