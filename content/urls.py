from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    # Content management URLs
    path('', views.ContentDashboardView.as_view(), name='dashboard'),
    path('resources/', views.ResourceListView.as_view(), name='resources'),
    path('resources/<int:resource_id>/', views.ResourceDetailView.as_view(), name='resource_detail'),

    # Content items management
    path('content-items/', views.ContentItemListView.as_view(), name='content_items'),
    path('content-items/<int:content_item_id>/', views.ContentItemDetailView.as_view(), name='content_item_detail'),
    path('content-items/create/', views.CreateContentItemView.as_view(), name='create_content_item'),

    # Interactive exercises
    path('exercises/', views.InteractiveExerciseListView.as_view(), name='exercises'),
    path('exercises/<int:exercise_id>/', views.InteractiveExerciseDetailView.as_view(), name='exercise_detail'),

    # Content libraries
    path('libraries/', views.ContentLibraryListView.as_view(), name='libraries'),
    path('libraries/<int:library_id>/', views.ContentLibraryDetailView.as_view(), name='library_detail'),

    # Search
    path('search/', views.ContentSearchView.as_view(), name='search'),
]
