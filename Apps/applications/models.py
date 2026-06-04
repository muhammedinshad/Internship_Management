from django.db import models
from django.conf import settings
from Apps.internships.models import Internship


class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    internship = models.ForeignKey(
        Internship,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'applications'
        unique_together = ('student', 'internship')
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['internship']),
        ]

    def __str__(self):
        return f"{self.student.username} → {self.internship.title}"