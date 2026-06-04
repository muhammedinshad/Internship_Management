from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Internship
from .serializers import InternshipSerializer


class InternshipListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        try:
            internships = Internship.objects.all()
            serializer = InternshipSerializer(internships, many=True)
            return Response({
                "success": True,
                "message": "Internships fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            if request.user.role != 'company':
                return Response({
                    "success": False,
                    "message": "Only company accounts can create internships"
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = InternshipSerializer(data=request.data)

            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Validation failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save(company=request.user)

            return Response({
                "success": True,
                "message": "Internship created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InternshipDetailView(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_object(self, pk):
        try:
            return Internship.objects.get(pk=pk)
        except Internship.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            internship = self.get_object(pk)
            if not internship:
                return Response({
                    "success": False,
                    "message": "Internship not found"
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = InternshipSerializer(internship)
            return Response({
                "success": True,
                "message": "Internship fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            internship = self.get_object(pk)
            if not internship:
                return Response({
                    "success": False,
                    "message": "Internship not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # Owner check
            if internship.company != request.user:
                return Response({
                    "success": False,
                    "message": "You are not authorized to update this internship"
                }, status=status.HTTP_403_FORBIDDEN)

            serializer = InternshipSerializer(internship, data=request.data, partial=True)

            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": "Validation failed",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            return Response({
                "success": True,
                "message": "Internship updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            internship = self.get_object(pk)
            if not internship:
                return Response({
                    "success": False,
                    "message": "Internship not found"
                }, status=status.HTTP_404_NOT_FOUND)

            # Owner check
            if internship.company != request.user:
                return Response({
                    "success": False,
                    "message": "You are not authorized to delete this internship"
                }, status=status.HTTP_403_FORBIDDEN)

            internship.delete()
            return Response({
                "success": True,
                "message": "Internship deleted successfully"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "success": False,
                "message": "Something went wrong",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)