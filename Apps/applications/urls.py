from django.urls import path
from .views import ApplyInternshipView, ListApplicationsView, UpdateApplicationStatusView

urlpatterns = [
    path('apply/', ApplyInternshipView.as_view(), name='apply-internship'),
    path('', ListApplicationsView.as_view(), name='list-applications'),
    path('<int:pk>/status/', UpdateApplicationStatusView.as_view(), name='update-status'),
]