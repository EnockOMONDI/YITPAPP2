from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, View, CreateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from .models import Resource, ContentItem, InteractiveExercise, ContentLibrary, LibraryItem


class ContentDashboardView(LoginRequiredMixin, TemplateView):
    """Content management dashboard"""
    template_name = 'lms/content/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Content statistics
        context['total_resources'] = Resource.objects.filter(is_published=True).count()
        context['total_content_items'] = ContentItem.objects.filter(is_published=True).count()
        context['total_exercises'] = InteractiveExercise.objects.count()

        # User's recent activity - simplified without ContentAccess model
        context['recent_resources'] = Resource.objects.filter(
            is_published=True
        ).order_by('-created_at')[:5]

        # Popular content
        context['popular_resources'] = Resource.objects.filter(
            is_published=True
        ).order_by('-view_count')[:5]

        return context


class ContentLibraryView(TemplateView):
    """Main content library"""
    template_name = 'lms/content/library.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all content types
        context['resources'] = Resource.objects.filter(is_published=True)[:6]
        context['content_items'] = ContentItem.objects.filter(is_published=True)[:6]
        context['exercises'] = InteractiveExercise.objects.all()[:6]

        # Libraries
        context['libraries'] = ContentLibrary.objects.all()

        return context


class ResourceListView(ListView):
    """List all resources"""
    model = Resource
    template_name = 'lms/content/resources.html'
    context_object_name = 'resources'
    paginate_by = 12

    def get_queryset(self):
        queryset = Resource.objects.filter(is_published=True)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['libraries'] = ContentLibrary.objects.all()
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_library'] = self.request.GET.get('library', '')
        return context


class ResourceDetailView(DetailView):
    """Resource detail view"""
    model = Resource
    template_name = 'lms/content/resource_detail.html'
    context_object_name = 'resource'
    pk_url_kwarg = 'resource_id'

    def get_object(self):
        resource = super().get_object()

        # Increment view count if user is authenticated
        if self.request.user.is_authenticated:
            resource.view_count += 1
            resource.save()

        return resource


class ContentItemListView(ListView):
    """List all content items"""
    model = ContentItem
    template_name = 'lms/content/content_items.html'
    context_object_name = 'content_items'
    paginate_by = 12

    def get_queryset(self):
        queryset = ContentItem.objects.filter(is_published=True)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        # Content type filter
        content_type = self.request.GET.get('content_type')
        if content_type:
            queryset = queryset.filter(content_type=content_type)

        return queryset.order_by('-created_at')


class ContentItemDetailView(DetailView):
    """Content item detail view"""
    model = ContentItem
    template_name = 'lms/content/content_item_detail.html'
    context_object_name = 'content_item'
    pk_url_kwarg = 'content_item_id'

    def get_object(self):
        content_item = super().get_object()

        # Increment view count if user is authenticated
        if self.request.user.is_authenticated:
            content_item.view_count += 1
            content_item.save()

        return content_item


class CreateContentItemView(LoginRequiredMixin, CreateView):
    """Create new content item"""
    model = ContentItem
    template_name = 'lms/content/create_content_item.html'
    fields = ['title', 'description', 'content_type', 'content', 'file_attachment']

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Content item created successfully!')
        return super().form_valid(form)


class InteractiveExerciseListView(ListView):
    """Interactive exercises library"""
    model = InteractiveExercise
    template_name = 'lms/content/exercises.html'
    context_object_name = 'exercises'
    paginate_by = 12

    def get_queryset(self):
        queryset = InteractiveExercise.objects.all()

        # Filter by exercise type
        exercise_type = self.request.GET.get('type')
        if exercise_type:
            queryset = queryset.filter(exercise_type=exercise_type)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exercise_types'] = InteractiveExercise.EXERCISE_TYPES
        context['selected_type'] = self.request.GET.get('type', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class InteractiveExerciseDetailView(DetailView):
    """Interactive exercise detail view"""
    model = InteractiveExercise
    template_name = 'lms/content/exercise_detail.html'
    context_object_name = 'exercise'
    pk_url_kwarg = 'exercise_id'


class ContentLibraryListView(ListView):
    """List content libraries"""
    model = ContentLibrary
    template_name = 'lms/content/libraries.html'
    context_object_name = 'libraries'

    def get_queryset(self):
        queryset = ContentLibrary.objects.all()

        # Filter by library type
        library_type = self.request.GET.get('type')
        if library_type:
            queryset = queryset.filter(library_type=library_type)

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['library_types'] = ContentLibrary.LIBRARY_TYPES
        return context


class ContentLibraryDetailView(DetailView):
    """Content library detail view"""
    model = ContentLibrary
    template_name = 'lms/content/library_detail.html'
    context_object_name = 'library'
    pk_url_kwarg = 'library_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        library = self.object

        # Get items in this library
        context['library_items'] = LibraryItem.objects.filter(
            library=library
        ).order_by('sort_order')

        return context


# Simplified content views using available models


class ContentSearchView(TemplateView):
    """Search across all content"""
    template_name = 'lms/content/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')

        if query:
            # Search across available content types
            context['resources'] = Resource.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                is_published=True
            )[:10]

            context['content_items'] = ContentItem.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                is_published=True
            )[:10]

            context['exercises'] = InteractiveExercise.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )[:10]

        context['query'] = query
        return context
