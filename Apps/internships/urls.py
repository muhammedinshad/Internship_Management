from django.urls import path
from .views import InternshipListCreateView, InternshipDetailView

urlpatterns = [
    path('', InternshipListCreateView.as_view(), name='internship-list-create'),
    path('<int:pk>/', InternshipDetailView.as_view(), name='internship-detail'),
]