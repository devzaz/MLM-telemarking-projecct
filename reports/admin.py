from django.contrib import admin
from .models import Report, ReportExport

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id','name','model','created_by','created_at','schedule')
    search_fields = ('name','model')

@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ('id','report','status','requested_by','created_at','file_path')
    list_filter = ('status',)
