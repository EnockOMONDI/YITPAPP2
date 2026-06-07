from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from events.models import Event, EventCategory


class Command(BaseCommand):
    help = "Seed the database with the Free Mentorship Session event."

    def handle(self, *args, **options):
        tz = timezone.get_current_timezone()
        start_dt = timezone.make_aware(datetime(2026, 1, 31, 10, 0), tz)

        title = "Free Mentorship Session"
        category_name = "Mentorship Session"
        content = (
            "<p><strong>The Youth Impact Training Programme (YITP)</strong> in collaboration "
            "with Wealthy Healthy SHG invites you to a free mentorship session.</p>"
            "<p><strong>Speaker:</strong> Mwali Muyumbu (Fred.Muyumbu), talent and life coach.</p>"
            "<p><strong>Time:</strong> 10:00 AM – 12:30 PM (EAT)</p>"
            "<p><strong>Topics:</strong> Soft Skills That Build Financial Freedom; "
            "How to Start &amp; Grow a Sustainable Business.</p>"
            "<p><strong>Why attend:</strong> Practical life &amp; business skills; "
            "Real mentorship from experienced leaders; Learn how to create income &amp; "
            "sustainable opportunities; FREE &amp; open to all youths.</p>"
            "<p><strong>Venue:</strong> Mathare North Living Word Church.</p>"
            "<p><strong>Register:</strong> www.youthimpactglobal.com/events</p>"
            "<p><strong>Call:</strong> 0768 218914 / 0722 646 958</p>"
        )

        with transaction.atomic():
            category, _ = EventCategory.objects.get_or_create(
                name=category_name,
                defaults={"slug": slugify(category_name), "active": True},
            )
            if not category.active:
                category.active = True
                category.save(update_fields=["active"])

            event, created = Event.objects.get_or_create(
                title=title,
                date=start_dt,
                defaults={
                    "event_type": "PHYSICAL",
                    "location": "Mathare North Living Word Church",
                    "content": content,
                    "featured": True,
                    "category": category,
                },
            )

            if not created:
                event.event_type = "PHYSICAL"
                event.location = "Mathare North Living Word Church"
                event.content = content
                event.featured = True
                event.category = category
                event.save()

            event.tags.set(["mentorship", "soft-skills", "business", "youth"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded event '{event.title}' for {event.date} (id={event.id})."
            )
        )
