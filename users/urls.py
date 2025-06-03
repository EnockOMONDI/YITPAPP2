from django.urls import path
from blogapp import views
from . import views 


app_name = 'users'

urlpatterns = [
    path('', views.home, name='home'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('programs/', views.programs, name='programs'),
    path('ourteam/', views.ourteam, name='ourteam'),
    path('contactus/', views.contactus, name='contactus'),


]

