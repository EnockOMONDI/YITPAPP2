from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def mark_redirect_after_login(sender, request, user, **kwargs):
    """
    Flag the session so the next page load can smart-redirect the user
    to their last lesson/dashboard, while still allowing them to browse
    marketing pages later without being forced off.
    """
    if request is None:
        return
    request.session['redirect_after_login'] = True
