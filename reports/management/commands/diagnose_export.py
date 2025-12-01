# reports/management/commands/diagnose_export.py
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from reports.models import Report, ReportExport
from reports.tasks import generate_report

class Command(BaseCommand):
    help = "Create a ReportExport for a report and optionally run the generate_report task synchronously for diagnosis."

    def add_arguments(self, parser):
        parser.add_argument('report_id', nargs='?', type=int, help='ID of the Report to diagnose. If omitted, uses the most recent.')
        parser.add_argument('--sync', action='store_true', help='Run the generate_report task synchronously (in-process) for quick debugging.')
        parser.add_argument('--show-latest-exports', action='store_true', help='Show latest 10 ReportExport rows (helper).')

    def handle(self, *args, **options):
        report_id = options.get('report_id')
        sync = options.get('sync', False)
        show_latest = options.get('show_latest_exports', False)

        if show_latest:
            self.stdout.write("Latest ReportExport rows:")
            for r in ReportExport.objects.order_by('-created_at')[:10]:
                self.stdout.write(f"  id={r.pk} report={r.report_id} status={r.status} file_path={r.file_path} error={(r.error[:200] + '...') if r.error else None}")
            return

        if report_id is None:
            rpt = Report.objects.order_by('-created_at').first()
            if not rpt:
                raise CommandError("No Report found in DB. Create one first or provide report_id.")
            report_id = rpt.pk
            self.stdout.write(f"Using most recent report id={report_id} (name='{rpt.name}')")
        else:
            try:
                rpt = Report.objects.get(pk=report_id)
            except Report.DoesNotExist:
                raise CommandError(f"Report with id={report_id} not found.")

        # create an export record
        exp = ReportExport.objects.create(report=rpt, requested_by=None, status='queued')
        self.stdout.write(f"Created ReportExport id={exp.pk} status={exp.status}")

        # show pre-task DB row
        exp.refresh_from_db()
        self.stdout.write(f"  pre-task: status={exp.status} file_path={exp.file_path} error={exp.error}")

        if sync:
            self.stdout.write("Running generate_report synchronously (apply) ...")
            # call task synchronously; returns AsyncResult-like object for .get()
            res = generate_report.apply(args=(report_id, exp.pk))
            try:
                result = res.get(timeout=60)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Task raised exception: {e}"))
                result = None

            self.stdout.write(f"Task returned: {result}")

            # refresh and show DB row after running
            exp.refresh_from_db()
            self.stdout.write(f"  post-task: status={exp.status} file_path={exp.file_path} error={(exp.error[:1000] + '...') if exp.error else None}")

            # check file existence if file_path present
            if exp.file_path:
                full = os.path.join(settings.MEDIA_ROOT, exp.file_path)
                exists = os.path.exists(full)
                self.stdout.write(f"  file exists: {exists} -> {full}")
            else:
                self.stdout.write("  no file_path set on export record.")
        else:
            self.stdout.write("Synchronous run not requested (--sync). Use Celery to process queued jobs or run with --sync for a test.")
            self.stdout.write("Note: after enqueue you'll need to run celery worker to pick up the job.")
