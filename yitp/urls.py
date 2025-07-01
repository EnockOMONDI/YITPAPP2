from django.urls import path
from . import views
from events.views import event_list

app_name = 'yitp'  # This helps with URL namespacing

urlpatterns = [
    path('', views.home, name='home'),
    path('web_courses_list/', views.web_courses_list, name='web_courses_list'),
    path('documentation/', views.documentation, name='documentation'),
    path('about/', views.about, name='about'),
    path('team/', views.team, name='team'),
    path('registration/', views.registration_redirect, name='registration'),
    path('registration2/', views.registration2, name='registration2'),
    path('join/', views.registration2, name='join'),  # Unified registration endpoint
    path('welcome/', views.welcome, name='welcome'),
    path('events/', event_list, name='events'),
    path('faqs/', views.faqs, name='faqs'),
    path('contact/', views.contact, name='contact'),
    path('coursedetail1/', views.coursedetail1, name='coursedetail1'),
    path('coursedetail2/', views.coursedetail2, name='coursedetail2'),
    path('coursedetail3/', views.coursedetail3, name='coursedetail3'),
    path('coursedetail4/', views.coursedetail4, name='coursedetail4'),
    path('coursedetail5/', views.coursedetail5, name='coursedetail5'),
    path('coursedetail6/', views.coursedetail6, name='coursedetail6'),
]