"""
YITP Blog Import/Export Resources
Comprehensive Excel import/export functionality for blog posts
"""

from import_export import resources, fields, widgets
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, DateTimeWidget
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from taggit.models import Tag
from .models import Post, Category, Comment
import logging

logger = logging.getLogger(__name__)


class CategoryWidget(ForeignKeyWidget):
    """Custom widget for Category foreign key handling"""
    
    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        
        # Try to get existing category by title
        try:
            return self.model.objects.get(title__iexact=value)
        except self.model.DoesNotExist:
            # Create new category if it doesn't exist
            slug = slugify(value)
            # Ensure unique slug
            original_slug = slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            category = Category.objects.create(
                title=value,
                slug=slug,
                active=True
            )
            logger.info(f"Created new category: {value} with slug: {slug}")
            return category


class TagsWidget(ManyToManyWidget):
    """Custom widget for handling tags"""
    
    def clean(self, value, row=None, **kwargs):
        if not value:
            return self.model.objects.none()
        
        # Split tags by comma and clean them
        tag_names = [tag.strip() for tag in str(value).split(',') if tag.strip()]
        tags = []
        
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tags.append(tag)
            if created:
                logger.info(f"Created new tag: {tag_name}")
        
        return self.model.objects.filter(name__in=[tag.name for tag in tags])


class UserWidget(ForeignKeyWidget):
    """Custom widget for User foreign key handling"""
    
    def clean(self, value, row=None, **kwargs):
        if not value:
            return None
        
        # Try to find user by username or email
        try:
            if '@' in str(value):
                return User.objects.get(email=value)
            else:
                return User.objects.get(username=value)
        except User.DoesNotExist:
            logger.warning(f"User not found: {value}")
            return None


class PostResource(resources.ModelResource):
    """
    Resource class for Post model import/export
    Handles Excel import/export with comprehensive validation and error handling
    """
    
    # Define custom fields with widgets
    title = fields.Field(
        column_name='title',
        attribute='title',
        widget=widgets.CharWidget()
    )
    
    content = fields.Field(
        column_name='content',
        attribute='content',
        widget=widgets.CharWidget()
    )
    
    author = fields.Field(
        column_name='author',
        attribute='Author',  # Note: model field is 'Author' with capital A
        widget=widgets.CharWidget()
    )
    
    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=CategoryWidget(Category, 'title')
    )
    
    tags = fields.Field(
        column_name='tags',
        attribute='tags',
        widget=TagsWidget(Tag, separator=',')
    )
    
    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=UserWidget(User, 'username')
    )
    
    status = fields.Field(
        column_name='status',
        attribute='status',
        widget=widgets.CharWidget()
    )
    
    featured = fields.Field(
        column_name='featured',
        attribute='featured',
        widget=widgets.BooleanWidget()
    )
    
    trending = fields.Field(
        column_name='trending',
        attribute='trending',
        widget=widgets.BooleanWidget()
    )
    
    publication_date = fields.Field(
        column_name='publication_date',
        attribute='date',
        widget=DateTimeWidget(format='%Y-%m-%d %H:%M:%S')
    )
    
    featured_image_url = fields.Field(
        column_name='featured_image_url',
        attribute='image',
        widget=widgets.CharWidget()
    )
    
    meta_description = fields.Field(
        column_name='meta_description',
        attribute='meta_description',
        widget=widgets.CharWidget(),
        readonly=True  # This field doesn't exist in model, for future use
    )
    
    slug = fields.Field(
        column_name='slug',
        attribute='pid',  # Using pid as slug equivalent
        widget=widgets.CharWidget(),
        readonly=True
    )
    
    views = fields.Field(
        column_name='views',
        attribute='views',
        widget=widgets.IntegerWidget(),
        readonly=True
    )

    class Meta:
        model = Post
        fields = (
            'id', 'title', 'content', 'author', 'category', 'tags', 'user',
            'status', 'featured', 'trending', 'publication_date', 
            'featured_image_url', 'meta_description', 'slug', 'views'
        )
        export_order = (
            'id', 'title', 'author', 'category', 'tags', 'status',
            'featured', 'trending', 'publication_date', 'content',
            'featured_image_url', 'meta_description', 'slug', 'views'
        )
        import_id_fields = ('id',)
        skip_unchanged = True
        report_skipped = True
        use_bulk = True
        batch_size = 100

    def before_import_row(self, row, **kwargs):
        """
        Validate and clean data before importing each row
        """
        # Validate required fields
        if not row.get('title'):
            return  # Skip row instead of raising exception

        # Validate status
        valid_statuses = ['draft', 'in_review', 'published']
        status = row.get('status', 'draft')
        if status and str(status).lower() in valid_statuses:
            row['status'] = str(status).lower()
        else:
            row['status'] = 'draft'

        # Set default author if not provided
        if not row.get('author'):
            row['author'] = 'YITP Admin'

        # Handle boolean fields
        for bool_field in ['featured', 'trending']:
            value = row.get(bool_field, '')
            if isinstance(value, bool):
                row[bool_field] = value
            elif str(value).lower() in ['true', '1', 'yes', 'on']:
                row[bool_field] = True
            else:
                row[bool_field] = False

        # Handle publication date
        if not row.get('publication_date'):
            row['publication_date'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

    def after_import_row(self, row, row_result, **kwargs):
        """
        Post-processing after importing each row
        """
        if row_result.import_type == 'new':
            logger.info(f"Successfully imported new post: {row.get('title')}")
        elif row_result.import_type == 'update':
            logger.info(f"Successfully updated post: {row.get('title')}")

    def skip_row(self, instance, original, row, import_validation_errors=None):
        """
        Skip rows with validation errors
        """
        if import_validation_errors:
            logger.error(f"Skipping row due to validation errors: {import_validation_errors}")
            return True
        return super().skip_row(instance, original, row, import_validation_errors)


class CategoryResource(resources.ModelResource):
    """Resource class for Category model import/export"""
    
    class Meta:
        model = Category
        fields = ('id', 'title', 'slug', 'active')
        export_order = ('id', 'title', 'slug', 'active')
        import_id_fields = ('id',)


class CommentResource(resources.ModelResource):
    """Resource class for Comment model import/export"""
    
    post = fields.Field(
        column_name='post',
        attribute='post',
        widget=ForeignKeyWidget(Post, 'title')
    )
    
    class Meta:
        model = Comment
        fields = ('id', 'post', 'full_name', 'email', 'comment', 'date', 'active')
        export_order = ('id', 'post', 'full_name', 'email', 'comment', 'date', 'active')
        import_id_fields = ('id',)
