from django.db import models
from django.conf import settings
from django.utils import timezone

class Report(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    file_path = models.FileField(upload_to='reports/')
    is_archived = models.BooleanField(default=False)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    publish_date = models.DateField(auto_now_add=True, null=True)

    def __str__(self):
        return self.name