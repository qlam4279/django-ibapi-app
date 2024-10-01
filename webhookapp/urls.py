from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    #path('webhook/', views.webhook, name='webhook'),
    re_path(r'^webhook/?$', views.webhook, name='webhook'),
    path('requests/', views.show_requests, name='show_requests'),
    path('delete_request/', views.delete_request, name='delete_request'),
    path('documentation/', views.documentation, name='documentation'),
    path('trades/', views.trades, name='trades'),
    path('refresh_trades/', views.refresh_trades, name='refresh_trades'),  # Route for refreshing trades via AJAX
]