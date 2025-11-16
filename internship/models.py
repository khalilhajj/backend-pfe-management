from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class Internship(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected'),
        (3, 'In Progress'),
        (4, 'Completed'),
    ]
    TYPE_CHOICES = [
        ('PFE', 'Projet de Fin d\'Études'),
        ('Stage', 'Stage'),
        ('Internship', 'Internship'),
    ]
    student_id=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='internships'
    )
    teacher_id=models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_internships',
        null=True,
        blank=True,
    )
    type = models.CharField(max_length=100)
    company_name = models.CharField(max_length=255)
    cahier_de_charges = models.FileField(upload_to='cahiers_de_charges/')
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    start_date = models.DateField()
    description = models.TextField(null=True, blank=True)
    end_date = models.DateField()
    title = models.CharField(max_length=255, default='Untitled')
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
class TeacherInvitation(models.Model):
    STATUS_CHOICES = [
        (0, 'Pending'),
        (1, 'Accepted'),
        (2, 'Rejected'),
    ]
    internship = models.ForeignKey(
        Internship,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations'
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True,null=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['internship', 'teacher']  # Prevent duplicate invitations

    def __str__(self):
        return f"Invitation from {self.student.username} to {self.teacher.username}"

class Soutenance(models.Model):
    internship = models.ForeignKey(
        Internship,
        on_delete=models.CASCADE,
        related_name='soutenances'
    )
    date = models.DateField()
    time = models.TimeField()
    room = models.CharField(max_length=255)
    grade= models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Soutenance for {self.internship} on {self.date} at {self.time}"
    
class Jury(models.Model):
    soutenance = models.ForeignKey(
        Soutenance,
        on_delete=models.CASCADE,
        related_name='juries'
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='jury_memberships'
    )

    def __str__(self):
        return f"Jury member {self.member} for {self.soutenance}"
