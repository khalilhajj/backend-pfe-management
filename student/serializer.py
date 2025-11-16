from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'name', 'description', 'file_path', 'is_archived', 'added_by', 'publish_date']
        read_only_fields = ['added_by', 'publish_date']