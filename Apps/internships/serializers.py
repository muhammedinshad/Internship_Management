from rest_framework import serializers
from .models import Internship


class InternshipSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.username', read_only=True)

    class Meta:
        model = Internship
        fields = [
            'id', 'title', 'description', 'location',
            'company_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'company_name', 'created_at', 'updated_at']

