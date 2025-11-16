import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify

from bs4 import BeautifulSoup
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from courses.models import Course, Module


class Command(BaseCommand):
    help = (
        "Export each lesson in the specified module as a standalone structured PDF. "
        "Default course is 'Youth Impact Training Programme (YITP)' and module "
        "'Understanding Purpose in Life (UPL)'."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--course-title",
            default="Youth Impact Training Programme (YITP)",
            help="Course title to pull data from (default: %(default)s)",
        )
        parser.add_argument(
            "--module-title",
            default="Understanding Purpose in Life (UPL)",
            help="Module title to export (default: %(default)s)",
        )
        parser.add_argument(
            "--output-dir",
            default="exports/yitp_upl_lessons",
            help="Directory to place the generated PDFs (default: %(default)s)",
        )

    def handle(self, *args, **options):
        course_title = options["course_title"]
        module_title = options["module_title"]
        output_dir = Path(options["output_dir"]).resolve()

        course = (
            Course.objects.filter(title__iexact=course_title)
            .order_by("title")
            .first()
        )
        if not course:
            raise CommandError(f"Course titled '{course_title}' not found.")

        module = (
            Module.objects.filter(course=course, title__iexact=module_title)
            .order_by("sort_order")
            .first()
        )
        if not module:
            raise CommandError(
                f"Module '{module_title}' was not found for course '{course.title}'."
            )

        lessons = module.lessons.order_by("sort_order").all()
        if not lessons:
            raise CommandError(
                f"No lessons found in '{module_title}' for course '{course.title}'."
            )

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise CommandError(
                f"Unable to create output directory '{output_dir}'. "
                "Pick a writable path (e.g. ./exports/lessons) or run as a user "
                f"with permissions. Original error: {exc}"
            ) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Exporting {lessons.count()} lessons from '{module.title}' "
                f"({course.title}) into {output_dir}"
            )
        )

        for index, lesson in enumerate(lessons, start=1):
            filename = f"{index:02d}-{slugify(lesson.title) or 'lesson'}.pdf"
            file_path = output_dir / filename
            self._render_lesson_pdf(lesson, file_path)
            self.stdout.write(f"  • {lesson.title} → {file_path.name}")

        self.stdout.write(
            self.style.SUCCESS(f"Completed export to {output_dir} (PDF per lesson).")
        )

    def _render_lesson_pdf(self, lesson, file_path: Path):
        """Build a structured PDF for the provided lesson."""
        doc = SimpleDocTemplate(
            str(file_path),
            pagesize=LETTER,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.9 * inch,
            bottomMargin=0.9 * inch,
        )

        styles = getSampleStyleSheet()
        heading_style = styles["Heading1"]
        heading_style.spaceAfter = 12

        subheading_style = styles["Heading3"]
        subheading_style.spaceBefore = 12
        subheading_style.spaceAfter = 6

        body_style = styles["BodyText"]
        body_style.leading = 14

        bullet_style = ParagraphStyle(
            "Bullet",
            parent=body_style,
            bulletIndent=12,
            leftIndent=18,
            spaceBefore=2,
        )

        story = []
        story.append(Paragraph(lesson.title, heading_style))
        story.append(
            Paragraph(
                f"Module: {lesson.module.title} | Course: {lesson.module.course.title}",
                styles["Italic"],
            )
        )
        story.append(Spacer(1, 12))

        metadata = [
            ["Content Type", lesson.get_content_type_display()],
            ["Estimated Duration", f"{lesson.estimated_duration} minutes"],
            ["Mandatory", "Yes" if lesson.is_mandatory else "Optional"],
            ["Published", "Yes" if lesson.is_published else "Draft"],
        ]
        if lesson.video_url:
            metadata.append(["Video URL", lesson.video_url])
        if lesson.document_src:
            metadata.append(["Document URL", lesson.document_src])
        if lesson.audio_url:
            metadata.append(["Audio URL", lesson.audio_url])
        if lesson.presentation_file:
            metadata.append(["Presentation File", lesson.presentation_file.url])

        meta_table = Table(metadata, colWidths=[1.75 * inch, 4.3 * inch])
        meta_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        story.append(meta_table)

        if lesson.learning_objectives:
            story.append(Paragraph("Learning Objectives", subheading_style))
            for line in self._split_lines(lesson.learning_objectives):
                story.append(Paragraph(f"• {line}", bullet_style))

        if lesson.content:
            story.append(Paragraph("Lesson Content", subheading_style))
            content_text = self._extract_plain_text(lesson.content)
            for paragraph in self._split_paragraphs(content_text):
                story.append(Paragraph(paragraph, body_style))
                story.append(Spacer(1, 6))

        if lesson.resources:
            story.append(Paragraph("Additional Resources", subheading_style))
            for resource in lesson.resources:
                if isinstance(resource, dict):
                    label = resource.get("label") or resource.get("title") or "Resource"
                    url = resource.get("url") or ""
                    entry = f"{label}: {url}" if url else label
                else:
                    entry = str(resource)
                story.append(Paragraph(f"• {entry}", bullet_style))

        doc.build(story)

    def _extract_plain_text(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        return soup.get_text("\n", strip=True)

    def _split_paragraphs(self, text: str):
        for block in text.split("\n"):
            line = block.strip()
            if line:
                yield line

    def _split_lines(self, text: str):
        for line in text.splitlines():
            cleaned = line.strip("-• \t")
            if cleaned:
                yield cleaned
