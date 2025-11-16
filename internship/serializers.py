from rest_framework import serializers
from .models import Internship, TeacherInvitation
from authentication.models import User
import os

class InternshipSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    teacher_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Internship
        fields = [
            'id', 'student_id', 'student_name', 'teacher_id', 'teacher_name',
            'type', 'type_display', 'company_name', 'cahier_de_charges',
            'status', 'status_display', 'start_date', 'end_date',
            'description', 'title', 'created_at', 'updated_at'
        ]
        read_only_fields = ['student_id', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        """Get full name of student"""
        if obj.student_id:
            return f"{obj.student_id.first_name} {obj.student_id.last_name}".strip() or obj.student_id.username
        return None

    def get_teacher_name(self, obj):
        """Get full name of teacher"""
        if obj.teacher_id:
            return f"{obj.teacher_id.first_name} {obj.teacher_id.last_name}".strip() or obj.teacher_id.username
        return None

    def validate(self, data):
        """Validate internship dates"""
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError({
                    'end_date': 'End date must be after start date.'
                })
        return data

    def validate_cahier_de_charges(self, value):
        """Validate file size and type"""
        if value:
            # Max file size: 10MB
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError('File size must be less than 10MB.')
            
            # Allowed file types - check MIME type for security
            allowed_extensions = ['.pdf', '.doc', '.docx']
            allowed_mime_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            
            ext = os.path.splitext(value.name)[1].lower()
            
            # Validate extension
            if ext not in allowed_extensions:
                raise serializers.ValidationError(
                    'Only PDF, DOC, and DOCX files are allowed.'
                )
            
            # Validate MIME type for additional security
            if hasattr(value, 'content_type') and value.content_type not in allowed_mime_types:
                raise serializers.ValidationError(
                    'Invalid file type. Only PDF, DOC, and DOCX files are allowed.'
                )
        
        return value


class TeacherInvitationSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    teacher_name = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    internship_title = serializers.CharField(source='internship.title', read_only=True)
    
    class Meta:
        model = TeacherInvitation
        fields = [
            'id', 'internship', 'internship_title', 'student', 'student_name',
            'teacher', 'teacher_name', 'status', 'status_display',
            'message', 'created_at', 'updated_at'
        ]
        read_only_fields = ['student', 'created_at', 'updated_at']

    def get_student_name(self, obj):
        """Get full name of student"""
        if obj.student:
            return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.username
        return None

    def get_teacher_name(self, obj):
        """Get full name of teacher"""
        if obj.teacher:
            return f"{obj.teacher.first_name} {obj.teacher.last_name}".strip() or obj.teacher.username
        return None

    def validate(self, data):
        """Validate invitation"""
        teacher = data.get('teacher')
        
        # Check if teacher role is valid
        if teacher and hasattr(teacher, 'role') and teacher.role:
            if teacher.role.name != 'Teacher':
                raise serializers.ValidationError({
                    'teacher': 'Selected user is not a teacher.'
                })
        
        # Check for duplicate invitations (only during creation)
        if self.instance is None:
            internship = data.get('internship')
            if internship and teacher:
                existing = TeacherInvitation.objects.filter(
                    internship=internship,
                    teacher=teacher
                ).exists()
                if existing:
                    raise serializers.ValidationError(
                        'An invitation has already been sent to this teacher.'
                    )
        
        return data


class TeacherListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing teachers"""
    role_name = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'role_name', 'profile_picture']

    def get_role_name(self, obj):
        """Get role name safely"""
        if hasattr(obj, 'role') and obj.role:
            return obj.role.name
        return None

    def get_full_name(self, obj):
        """Get full name of user"""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username