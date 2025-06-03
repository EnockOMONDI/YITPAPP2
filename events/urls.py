from django.urls import include, path
from django.urls import path
from .views import event_list, event_detail

app_name = 'events'

urlpatterns = [
    path('', event_list, name='event_list'),
    path('<int:id>/', event_detail, name='event_detail'),  # Ensure this exists
]