# reports/views.py
import json
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, FileResponse, Http404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from .models import Report, ReportExport
from .tasks import generate_report
from django.utils.text import slugify
import os
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db.models import Prefetch
from .models import Report, ReportExport

def is_admin_or_telemarketer(user):
    return user.is_authenticated and (user.is_staff or getattr(user, 'role', '') in ('admin','telemarketer'))

@login_required
@user_passes_test(is_admin_or_telemarketer)
def report_builder(request):
    # simple UI, saves Report (filters as JSON)
    if request.method == 'POST':
        data = request.POST
        name = data.get('name') or "Untitled report"
        model = data.get('model')
        filters_json = data.get('filters_json') or '[]'
        try:
            filters = json.loads(filters_json)
        except Exception:
            filters = []
        slug = slugify(name)[:50]
        rpt = Report.objects.create(name=name, model=model, filters=filters, created_by=request.user, slug=slug)
        return redirect('reports:report_detail', report_id=rpt.pk)
    # show simple builder form
    return render(request, 'reports/report_builder.html', {
        'models': [
            # helpful list for UI; you can fill dynamically
            'commissions.Commission',
            'commissions.WalletTransaction',
            'referrals.ReferralConversion',
        ]
    })



# @require_POST
# @login_required
# @user_passes_test(is_admin_or_telemarketer)
# def enqueue_export(request, report_id):
#     """
#     Create a ReportExport and enqueue the celery task.
#     Returns JSON with export_id and a status_url to poll.
#     """
#     rpt = get_object_or_404(Report, pk=report_id)
#     exp = ReportExport.objects.create(report=rpt, requested_by=request.user, status='queued')
#     # call celery
#     generate_report.delay(rpt.pk, exp.pk)
#     status_url = reverse('reports:export_status', kwargs={'export_id': exp.pk})
#     return JsonResponse({'status': 'queued', 'export_id': exp.pk, 'status_url': status_url})

@require_POST
@login_required
@user_passes_test(is_admin_or_telemarketer)
def enqueue_export(request, report_id):
    """
    Create a ReportExport and enqueue the celery task.
    Returns JSON with export_id and a status_url to poll.
    """
    rpt = get_object_or_404(Report, pk=report_id)
    exp = ReportExport.objects.create(report=rpt, requested_by=request.user, status='queued')
    # call celery
    generate_report.delay(rpt.pk, exp.pk)
    status_url = reverse('reports:export_status', kwargs={'export_id': exp.pk})
    return JsonResponse({'status': 'queued', 'export_id': exp.pk, 'status_url': status_url})


@login_required
@user_passes_test(is_admin_or_telemarketer)
def export_status(request, export_id):
    """
    Return JSON status for a ReportExport.
    """
    exp = get_object_or_404(ReportExport, pk=export_id)
    data = {
        'id': exp.pk,
        'status': exp.status,
        'file_path': exp.file_path,
        'filename': exp.filename(),
        'error': exp.error,
        # download_url will point to the existing download endpoint
        'download_url': reverse('reports:download_export', kwargs={'export_id': exp.pk}) if exp.file_path else None,
    }
    return JsonResponse(data)
@login_required
@user_passes_test(is_admin_or_telemarketer)
def export_list(request):
    exports = ReportExport.objects.select_related('report','requested_by').order_by('-created_at')
    return render(request, 'reports/export_list.html', {'exports': exports})

@login_required
@user_passes_test(is_admin_or_telemarketer)
def download_export(request, export_id):
    exp = get_object_or_404(ReportExport, pk=export_id)
    # permit only staff or owner or requested_by
    if not (request.user.is_staff or exp.requested_by == request.user):
        return HttpResponseForbidden("You don't have permission to download this export.")
    if not exp.file_path:
        raise Http404("File not ready")
    full_path = os.path.join(settings.MEDIA_ROOT, exp.file_path)
    return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=exp.filename())


@login_required
@user_passes_test(is_admin_or_telemarketer)
def report_detail(request, report_id):
    """
    Show report details and allow user to enqueue an export.
    """
    rpt = get_object_or_404(Report, pk=report_id)
    return render(request, 'reports/detail.html', {
        'report': rpt,
    })



# @login_required
# @user_passes_test(is_admin_or_telemarketer)
# def reports_list(request):
#     """
#     Show all saved report definitions with an Export button for each.
#     Server-side shows Download if a 'done' export exists, or 'Queued/Running' if in progress.
#     """
#     # Prefetch latest export per report (most recent)
#     # We use a Prefetch that orders exports so that accessing rpt.exports.first() gives latest
#     exports_prefetch = Prefetch(
#         'exports',
#         queryset=ReportExport.objects.order_by('-created_at'),
#         to_attr='exports_prefetched'
#     )
#     reports = Report.objects.all().prefetch_related(exports_prefetch).order_by('-created_at')

#     # Build a dict mapping report_id -> latest_export (or None)
#     latest_map = {}
#     for rpt in reports:
#         latest = rpt.exports_prefetched[0] if getattr(rpt, 'exports_prefetched', None) else None
#         latest_map[rpt.pk] = latest

#     return render(request, "reports/list.html", {"reports": reports, "latest_map": latest_map})


@login_required
@user_passes_test(is_admin_or_telemarketer)
def reports_list(request):
    """
    Show all saved report definitions with an Export button for each.
    Attach rpt.latest_export so templates can render the correct action on refresh.
    """
    # Prefetch exports ordered by newest first
    exports_prefetch = Prefetch(
        'exports',
        queryset=ReportExport.objects.order_by('-created_at'),
        to_attr='exports_prefetched'
    )

    reports = list(Report.objects.all().prefetch_related(exports_prefetch).order_by('-created_at'))

    # Attach latest_export attribute (or None) to each report
    for rpt in reports:
        rpt.latest_export = rpt.exports_prefetched[0] if getattr(rpt, 'exports_prefetched', None) else None

    return render(request, "reports/list.html", {"reports": reports})