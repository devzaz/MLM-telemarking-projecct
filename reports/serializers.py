# reports/serializers.py
from rest_framework import serializers
from .models import Report, ReportExport, AlertRule

class ReportSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at', 'last_run_at')

class ReportExportSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    class Meta:
        model = ReportExport
        fields = ('id','report','status','created_at','completed_at','download_url','error')

    def get_download_url(self, obj):
        return obj.file_url()

class AlertRuleSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    class Meta:
        model = AlertRule
        fields = '__all__'
        read_only_fields = ('created_by','created_at')
