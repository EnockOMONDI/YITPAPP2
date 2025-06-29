from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from . models import Profile
from django.core.exceptions import ObjectDoesNotExist

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Create a profile for newly created users only"""
    if created:  # Only create profile for new users
        try:
            # Check if profile already exists
            if not hasattr(instance, 'profile'):
                Profile.objects.create(user=instance)
        except ObjectDoesNotExist:
            Profile.objects.create(user=instance)