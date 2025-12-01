import csv
import io
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from .forms import LeadForm, LeadNoteForm
from .models import Lead, LeadNote

User = get_user_model()

def is_telemarketer(user):
    return getattr(user, 'role', None) == 'telemarketer' or user.is_staff

@login_required
def lead_list(request):
    """
    Renders list page. DataTables will call the API endpoint for actual rows.
    """
    telemarketers = User.objects.filter(role='telemarketer')
    statuses = Lead.STATUS_CHOICES
    # Dashboard counts
    total = Lead.objects.count()
    converted = Lead.objects.filter(status=Lead.STATUS_CONVERTED).count()
    pending = Lead.objects.exclude(status=Lead.STATUS_CONVERTED).count()
    return render(request, 'crm/lead_list.html', {
        'telemarketers': telemarketers,
        'statuses': statuses,
        'dashboard': {'total': total, 'converted': converted, 'pending': pending}
    })

@login_required
def leads_api(request):
    """
    Returns JSON data for DataTables. Supports simple search/filter.
    """
    # Basic server-side list implementation (for moderate datasets)
    qs = Lead.objects.select_related('assigned_to', 'created_by').all()

    # Filtering by status/assigned
    status = request.GET.get('status')
    assigned = request.GET.get('assigned')
    q = request.GET.get('search[value]')  # DataTables search input key

    if status:
        qs = qs.filter(status=status)
    if assigned:
        qs = qs.filter(assigned_to_id=assigned)
    if q:
        qs = qs.filter(models.Q(name__icontains=q) | models.Q(email__icontains=q) | models.Q(phone__icontains=q))

    # ordering & pagination (basic)
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 25))
    total = qs.count()
    qs = qs[start:start + length]

    data = []
    for lead in qs:
        data.append({
            'id': lead.id,
            'name': lead.name,
            'email': lead.email or '',
            'phone': lead.phone or '',
            'status': lead.get_status_display(),
            'assigned_to': lead.assigned_to.username if lead.assigned_to else '',
            'created_at': lead.created_at.strftime('%Y-%m-%d %H:%M'),
            'actions': render_action_buttons(lead)
        })
    return JsonResponse({
        'draw': int(request.GET.get('draw', 1)),
        'recordsTotal': total,
        'recordsFiltered': total,
        'data': data
    })

def render_action_buttons(lead):
    edit = f'<a href="{reverse("crm:lead_update", args=[lead.id])}" class="btn btn-sm btn-primary">Edit</a>'
    view = f'<a href="{reverse("crm:lead_detail", args=[lead.id])}" class="btn btn-sm btn-secondary">View</a>'
    assign = f'<a href="{reverse("crm:lead_assign", args=[lead.id])}" class="btn btn-sm btn-info">Assign</a>'
    return f'{view} {edit} {assign}'

@login_required
def lead_create(request):
    if request.method == 'POST':
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.created_by = request.user
            lead.save()
            messages.success(request, "Lead created.")
            return redirect('crm:lead_list')
    else:
        form = LeadForm()
    return render(request, 'crm/lead_form.html', {'form': form, 'creating': True})

@login_required
def lead_update(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, "Lead updated.")
            return redirect('crm:lead_list')
    else:
        form = LeadForm(instance=lead)
    return render(request, 'crm/lead_form.html', {'form': form, 'creating': False, 'lead': lead})

@login_required
def lead_delete(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        lead.delete()
        messages.success(request, "Lead deleted.")
        return redirect('crm:lead_list')
    return render(request, 'crm/lead_delete_confirm.html', {'lead': lead})

@login_required
def lead_detail(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    note_form = LeadNoteForm()
    if request.method == 'POST' and 'add_note' in request.POST:
        note_form = LeadNoteForm(request.POST)
        if note_form.is_valid():
            note = note_form.save(commit=False)
            note.lead = lead
            note.author = request.user
            note.save()
            messages.success(request, "Note added.")
            return redirect('crm:lead_detail', pk=pk)
    return render(request, 'crm/lead_detail.html', {'lead': lead, 'note_form': note_form})

@login_required
@user_passes_test(lambda u: u.is_staff or getattr(u, 'role', '') == 'telemarketer')
def assign_lead(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.get(pk=int(user_id))
            if user.role != 'telemarketer' and not user.is_staff:
                messages.error(request, "Selected user is not a telemarketer.")
            else:
                lead.assigned_to = user
                lead.save()
                messages.success(request, "Lead assigned.")
        except Exception:
            messages.error(request, "Invalid user selected.")
        return redirect('crm:lead_detail', pk=pk)
    telemarketers = User.objects.filter(role='telemarketer')
    return render(request, 'crm/assign_lead.html', {'lead': lead, 'telemarketers': telemarketers})

@login_required
def import_leads_view(request):
    """
    Simple CSV import view. Columns: name,email,phone,status,assigned_referral_code(optional)
    """
    if request.method == 'POST':
        f = request.FILES.get('file')
        if not f:
            messages.error(request, "Please upload a CSV file.")
            return redirect('crm:lead_import_csv')
        try:
            text = f.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(text))
            created = 0
            errors = []
            with transaction.atomic():
                for i, row in enumerate(reader, start=1):
                    name = row.get('name') or row.get('Name')
                    if not name:
                        errors.append(f"Row {i}: missing name")
                        continue
                    email = row.get('email', '')
                    phone = row.get('phone', '')
                    status = row.get('status', Lead.STATUS_CONTACTED)
                    assigned_code = row.get('assigned_referral_code') or row.get('assigned_ref')
                    assigned_to = None
                    if assigned_code:
                        try:
                            assigned_user = User.objects.get(referral_code=assigned_code)
                            # ensure telemarketer
                            if assigned_user.role == 'telemarketer' or assigned_user.is_staff:
                                assigned_to = assigned_user
                        except User.DoesNotExist:
                            # ignore invalid assigned code
                            assigned_to = None
                    lead = Lead.objects.create(
                        name=name.strip(),
                        email=email.strip() if email else '',
                        phone=phone.strip() if phone else '',
                        status=status if status in dict(Lead.STATUS_CHOICES) else Lead.STATUS_CONTACTED,
                        assigned_to=assigned_to,
                        created_by=request.user
                    )
                    created += 1
            messages.success(request, f"Imported {created} leads. {len(errors)} rows had errors.")
            if errors:
                messages.warning(request, "Errors: " + "; ".join(errors[:5]))
            return redirect('crm:lead_list')
        except Exception as e:
            messages.error(request, f"Import failed: {e}")
            return redirect('crm:lead_import_csv')
    return render(request, 'crm/import_leads.html')
