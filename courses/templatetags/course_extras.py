from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    if dictionary and key is not None:
        return dictionary.get(key)
    return None

@register.filter
def split(value, delimiter):
    """Split a string by delimiter"""
    if value:
        return value.split(delimiter)
    return []

@register.filter
def default_if_none(value, default):
    """Return default if value is None"""
    if value is None:
        return default
    return value

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def lesson_accessible_for_user(lesson, user):
    """Check if lesson is accessible for the given user"""
    if lesson and user and hasattr(lesson, 'is_accessible_for_user'):
        try:
            return lesson.is_accessible_for_user(user)
        except Exception:
            return False, "Unable to check accessibility"
    return False, "Invalid lesson or user"

@register.filter
def quiz_accessible_for_user(quiz, user):
    """Check if quiz is accessible for the given user"""
    if quiz and user and hasattr(quiz, 'is_accessible_for_user'):
        try:
            return quiz.is_accessible_for_user(user)
        except Exception:
            return False, "Unable to check accessibility"
    return False, "Invalid quiz or user"
