import glob
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Export Module 2 static HTML lessons to PDFs in exports/module2/ (requires WeasyPrint)."

    def handle(self, *args, **options):
        try:
            from weasyprint import HTML  # type: ignore
        except ImportError:
            self.stdout.write(self.style.ERROR(
                "WeasyPrint is not installed. Install it with: pip install weasyprint"
            ))
            return

        # Locate the static/module2 directory
        static_root = Path(
            getattr(settings, "STATIC_ROOT", "")
            or (settings.STATICFILES_DIRS[0] if getattr(settings, "STATICFILES_DIRS", None) else "")
        )
        module_dir = static_root / "module2"
        if not module_dir.exists():
            self.stdout.write(self.style.ERROR(f"module2 directory not found at {module_dir}"))
            return

        export_dir = Path(settings.BASE_DIR) / "exports" / "module2"
        export_dir.mkdir(parents=True, exist_ok=True)

        html_files = sorted(glob.glob(str(module_dir / "lesson_*.html")))
        if not html_files:
            self.stdout.write(self.style.WARNING("No lesson_*.html files found in module2 directory."))
            return

        self.stdout.write(self.style.MIGRATE_HEADING("Exporting Module 2 lessons to PDF..."))

        base_url = str(static_root.resolve())
        for html_path in html_files:
            html_file = Path(html_path)
            pdf_name = html_file.with_suffix(".pdf").name
            out_path = export_dir / pdf_name

            HTML(filename=str(html_file), base_url=base_url).write_pdf(target=str(out_path))
            self.stdout.write(f" ✔ {html_file.name} -> {out_path}")

        self.stdout.write(self.style.SUCCESS(f"Export complete. PDFs saved to {export_dir}"))
