from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from html import unescape
from django.utils.html import strip_tags
from shortuuid.django_fields import ShortUUIDField
from pyuploadcare.dj.models import ImageField
from ckeditor.fields import RichTextField


BLOG_PUBLISH_STATUS = (
	("draft", "draft"),
	("in_review", "In Review"),
	("published", "Published"),
)



class Category(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.title 
        
    
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True )
    Author = models.CharField(max_length=1000)
    image = ImageField(blank=True, null=True, manual_crop="16:9")
    title = models.CharField(max_length=1000)
    content = RichTextField(max_length=10000)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = TaggableManager()
    status = models.CharField(choices=BLOG_PUBLISH_STATUS, max_length=100, default="in_review")
    featured = models.BooleanField(default=False)
    trending = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)
    pid = ShortUUIDField(length=10, max_length=25, alphabet="abcdefghijklmnopqrstuvxyz")

    class Meta:
        verbose_name = "Posts"
        verbose_name_plural = "Posts"
        ordering = ['-date']

    def __str__(self):
        return self.title[0:10]

    def get_read_time(self):
        string = self.content + unescape(strip_tags(self.content))
        total_words = len((string).split())

        return round(total_words / 200)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    full_name = models.CharField(max_length=1000)
    email = models.EmailField()
    comment = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.comment[0:20]
    


class StaticContent(models.Model):
    SECTION_CHOICES = [
        ('about_us', 'About Us'),
        ('mission', 'Our Mission'),
        ('vision', 'Vision'),
    ]

    section_name = models.CharField(max_length=100, choices=SECTION_CHOICES, unique=True)
    content = RichTextField()

    def __str__(self):
        return self.get_section_name_display()