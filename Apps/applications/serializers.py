from rest_framework import serializers
from .models import Application
from Apps.internships.serializers import InternshipSerializer


class ApplicationSerializer(serializers.ModelSerializer):
    internship_detail = InternshipSerializer(source='internship', read_only=True)
    student_name = serializers.CharField(source='student.username', read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'student_name', 'internship', 
            'internship_detail', 'status', 'applied_at'
        ]
        read_only_fields = ['id', 'student_name', 'status', 'applied_at', 'internship_detail']

    def validate_internship(self, value):
        request = self.context.get('request')

        if request.user.role != 'student':
            raise serializers.ValidationError("Only students can apply for internships.")

        if Application.objects.filter(student=request.user, internship=value).exists():
            raise serializers.ValidationError("You have already applied for this internship.")

        return value