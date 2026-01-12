from django.db import models

from tasks.models import Task
from tasks.models.Users import Users

class Activity_Log(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)   # ex: "status changed", "assigned", "updated", "commented"
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)

    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']