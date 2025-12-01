# reports/tasks.py
import csv
import os
import logging
from django.conf import settings
from celery import shared_task
from django.apps import apps
from django.utils import timezone
from .models import Report, ReportExport

logger = logging.getLogger(__name__)

def apply_filters_to_queryset(queryset, filters):
    """Simple filter engine. Extend ops as needed."""
    from django.db.models import Q
    q = Q()
    for f in filters:
        field = f.get('field')
        op = f.get('op', 'exact')
        value = f.get('value')
        if op == 'exact':
            q &= Q(**{field: value})
        elif op == 'icontains':
            q &= Q(**{f"{field}__icontains": value})
        elif op == 'gte':
            q &= Q(**{f"{field}__gte": value})
        elif op == 'lte':
            q &= Q(**{f"{field}__lte": value})
        elif op == 'in':
            q &= Q(**{f"{field}__in": value})
        # add more operators as required
    return queryset.filter(q)

@shared_task(bind=True)
def generate_report(self, report_id, export_id=None):
    logger.info("generate_report called report_id=%s export_id=%s", report_id, export_id)
    try:
        report = Report.objects.get(pk=report_id)
    except Report.DoesNotExist:
        logger.error("report %s not found", report_id)
        return {'error': 'report_not_found'}

    export = None
    if export_id:
        try:
            export = ReportExport.objects.get(pk=export_id)
            export.status = 'running'
            export.save()
        except ReportExport.DoesNotExist:
            export = None

    try:
        app_label, model_name = report.model.split('.')
        Model = apps.get_model(app_label, model_name)
    except Exception as e:
        logger.exception("invalid model for report %s: %s", report_id, e)
        if export:
            export.status = 'error'
            export.error = str(e)
            export.save()
        return {'error': 'invalid_model', 'details': str(e)}

    qs = Model.objects.all()
    try:
        qs = apply_filters_to_queryset(qs, report.filters)
    except Exception as e:
        logger.exception("filter application failed for report %s: %s", report_id, e)
        if export:
            export.status = 'error'
            export.error = str(e)
            export.save()
        return {'error': 'filter_error', 'details': str(e)}

    # Build CSV
    # For now pick all fields from model._meta.fields
    fields = [f.name for f in Model._meta.fields]
    filename = f"report_{report.slug or report.pk}_{timezone.now().strftime('%Y%m%d%H%M%S')}.csv"
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        logger.error("MEDIA_ROOT not configured")
        if export:
            export.status = 'error'
            export.error = 'MEDIA_ROOT not configured'
            export.save()
        return {'error': 'no_media_root'}

    out_dir = os.path.join(media_root, 'report_exports')
    os.makedirs(out_dir, exist_ok=True)
    file_path = os.path.join(out_dir, filename)

    try:
        with open(file_path, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.writer(fh)
            writer.writerow(fields)
            for obj in qs.iterator():
                row = [getattr(obj, f) for f in fields]
                writer.writerow(row)
    except Exception as e:
        logger.exception("failed to write csv for report %s: %s", report_id, e)
        if export:
            export.status = 'error'
            export.error = str(e)
            export.save()
        return {'error': 'write_error', 'details': str(e)}

    if export:
        export.status = 'done'
        export.file_path = os.path.join('report_exports', filename)  # relative inside MEDIA_ROOT
        export.save()

    return {'ok': True, 'file': export.file_path if export else os.path.join('report_exports', filename)}
