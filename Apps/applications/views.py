from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Application
from .serializers import ApplicationSerializer


class ApplyInternshipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if request.user.role != 'student':
                return Response({
                    "success": False,
                    "message": "Only students can apply for internships"
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = ApplicationSerializer(
                data=request.data,
                context={'request': request}
            )

            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Validation failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(student=request.user)

            return Response({
                "success": True,
                "message": "Applied successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ListApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.user.role == 'student':
                applications = Application.objects.filter(
                    student=request.user
                ).select_related('internship', 'student')

            elif request.user.role == 'company':
                applications = Application.objects.filter(
                    internship__company=request.user
                ).select_related('internship', 'student')

            else:
                return Response({
                    "success": False,
                    "message": "Unauthorized"
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = ApplicationSerializer(applications, many=True)
            return Response({
                "success": True,
                "message": "Applications fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateApplicationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            if request.user.role != 'company':
                return Response({
                    "success": False,
                    "message": "Only companies can update application status"
                }, status=status.HTTP_403_FORBIDDEN)

            try:
                application = Application.objects.get(pk=pk)
            except Application.DoesNotExist:
                return Response({
                    "success": False,
                    "message": "Application not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # Owner check
            if application.internship.company != request.user:
                return Response({
                    "success": False,
                    "message": "You are not authorized to update this application"
                }, status=status.HTTP_403_FORBIDDEN)

            new_status = request.data.get('status')
            if new_status not in ['pending', 'accepted', 'rejected']:
                return Response({
                    "success": False,
                    "message": "Invalid status. Choose: pending, accepted, rejected"
                }, status=status.HTTP_400_BAD_REQUEST)

            application.status = new_status
            application.save()

            serializer = ApplicationSerializer(application)
            return Response({
                "success": True,
                "message": f"Application {new_status} successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)