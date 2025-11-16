from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404

from .models import Internship, TeacherInvitation
from .serializers import (
    InternshipSerializer,
    TeacherInvitationSerializer,
    TeacherListSerializer
)
from authentication.models import User, Role


class CreateInternshipView(APIView):
    """Create a new internship"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        request_body=InternshipSerializer,
        responses={
            201: InternshipSerializer,
            400: 'Bad Request',
            403: 'Forbidden - Only students can create internships'
        }
    )
    def post(self, request):
        # Check if user is a student
        if not request.user.role or request.user.role.name != 'Student':
            return Response({
                'error': 'Only students can create internships.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = InternshipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student_id=request.user, status=0)  # Pending status
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetStudentInternshipsView(APIView):
    """Get all internships for the authenticated student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        internships = Internship.objects.filter(student_id=request.user)
        serializer = InternshipSerializer(internships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetInternshipDetailView(APIView):
    """Get detailed information about a specific internship"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="Internship ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: InternshipSerializer,
            404: 'Not Found'
        }
    )
    def get(self, request, id):
        internship = get_object_or_404(Internship, id=id)
        
        # Check if user has access to this internship
        if internship.student_id != request.user and internship.teacher_id != request.user:
            return Response({
                'error': 'You do not have permission to view this internship.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = InternshipSerializer(internship)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ListTeachersView(APIView):
    """Get list of all teachers for sending invitations"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: TeacherListSerializer(many=True)
        }
    )
    def get(self, request):
        # Get Teacher role
        teacher_role = Role.objects.filter(name='Teacher').first()
        
        if not teacher_role:
            return Response({
                'error': 'Teacher role not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get all users with Teacher role
        teachers = User.objects.filter(role=teacher_role)
        serializer = TeacherListSerializer(teachers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SendTeacherInvitationView(APIView):
    """Send invitation to a teacher for internship supervision"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=TeacherInvitationSerializer,
        responses={
            201: TeacherInvitationSerializer,
            400: 'Bad Request',
            403: 'Forbidden'
        }
    )
    def post(self, request):
        # Check if user is a student
        if not request.user.role or request.user.role.name != 'Student':
            return Response({
                'error': 'Only students can send invitations.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Verify internship belongs to student
        internship_id = request.data.get('internship')
        internship = get_object_or_404(Internship, id=internship_id)
        
        if internship.student_id != request.user:
            return Response({
                'error': 'You can only send invitations for your own internships.'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = TeacherInvitationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=request.user, status=0)  # Pending
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GetStudentInvitationsView(APIView):
    """Get all invitations sent by the student"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        invitations = TeacherInvitation.objects.filter(student=request.user)
        serializer = TeacherInvitationSerializer(invitations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RespondToInvitationView(APIView):
    """Teacher responds to an invitation (accept/reject)"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='1 for Accept, 2 for Reject'
                )
            },
            required=['status']
        ),
        responses={
            200: TeacherInvitationSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found'
        }
    )
    def patch(self, request, id):
        # Check if user is a teacher
        if not request.user.role or request.user.role.name != 'Teacher':
            return Response({
                'error': 'Only teachers can respond to invitations.'
            }, status=status.HTTP_403_FORBIDDEN)

        invitation = get_object_or_404(TeacherInvitation, id=id)
        
        # Check if invitation is for this teacher
        if invitation.teacher != request.user:
            return Response({
                'error': 'You can only respond to invitations sent to you.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Check if already responded
        if invitation.status != 0:
            return Response({
                'error': 'This invitation has already been responded to.'
            }, status=status.HTTP_400_BAD_REQUEST)

        new_status = request.data.get('status')
        if new_status is None:
            return Response({
                'error': 'Status is required. Use 1 for Accept, 2 for Reject.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            new_status = int(new_status)
        except (ValueError, TypeError):
            return Response({
                'error': 'Invalid status format. Use 1 for Accept, 2 for Reject.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if new_status not in [1, 2]:
            return Response({
                'error': 'Invalid status. Use 1 for Accept, 2 for Reject.'
            }, status=status.HTTP_400_BAD_REQUEST)

        invitation.status = new_status
        invitation.save()

        # If accepted, assign teacher to internship
        if new_status == 1:
            internship = invitation.internship
            internship.teacher_id = request.user
            internship.status = 1  # Approved
            internship.save()

        serializer = TeacherInvitationSerializer(invitation)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetPendingInternshipsView(APIView):
    """Get all pending internships for admin review"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: InternshipSerializer(many=True),
            403: 'Forbidden - Only administrators can access'
        }
    )
    def get(self, request):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can view pending internships.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get all pending internships
        internships = Internship.objects.filter(status=0).order_by('-created_at')
        serializer = InternshipSerializer(internships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApproveInternshipView(APIView):
    """Admin approves an internship"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="Internship ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: InternshipSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found'
        }
    )
    def patch(self, request, id):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can approve internships.'
            }, status=status.HTTP_403_FORBIDDEN)

        internship = get_object_or_404(Internship, id=id)

        # Check if internship is pending
        if internship.status != 0:
            return Response({
                'error': 'Only pending internships can be approved.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Approve the internship
        internship.status = 1  # Approved
        internship.save()

        serializer = InternshipSerializer(internship)
        return Response({
            'message': 'Internship approved successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class RejectInternshipView(APIView):
    """Admin rejects an internship"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'id',
                openapi.IN_PATH,
                description="Internship ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'reason': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Reason for rejection (optional)'
                )
            }
        ),
        responses={
            200: InternshipSerializer,
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found'
        }
    )
    def patch(self, request, id):
        # Check if user is an administrator
        if not request.user.role or request.user.role.name != 'Administrator':
            return Response({
                'error': 'Only administrators can reject internships.'
            }, status=status.HTTP_403_FORBIDDEN)

        internship = get_object_or_404(Internship, id=id)

        # Check if internship is pending
        if internship.status != 0:
            return Response({
                'error': 'Only pending internships can be rejected.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Reject the internship
        internship.status = 2  # Rejected
        internship.save()

        # Optional: Store rejection reason (you might want to add a field to the model)
        reason = request.data.get('reason', '')

        serializer = InternshipSerializer(internship)
        return Response({
            'message': 'Internship rejected successfully.',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

class GetTeacherInvitationsView(APIView):
    """Get all invitations received by the teacher"""
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={
            200: TeacherInvitationSerializer(many=True),
            403: 'Forbidden - Only teachers can access'
        }
    )
    def get(self, request):
        # Check if user is a teacher
        if not request.user.role or request.user.role.name != 'Teacher':
            return Response({
                'error': 'Only teachers can view invitations.'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get all invitations for this teacher
        invitations = TeacherInvitation.objects.filter(
            teacher=request.user
        ).select_related('student', 'internship')
        
        serializer = TeacherInvitationSerializer(invitations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)