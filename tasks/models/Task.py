from django.db import models

from tasks.models.Project import Project
from tasks.models.Users import Users

class Task(models.Model):
    task_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    status = models.CharField(
        max_length=255,
        choices=(
            ('Todo', 'todo'),
            ('In Progress', 'in progress'),
            ('Under Review', 'under review'),
            ('Done', 'done')
        )
    )
    priority = models.CharField(
        max_length=255,
        choices=(
            ('high', 'High'),
            ('medium', 'Medium'),
            ('Low', 'low')
        )
    )
    due_date = models.DateTimeField(auto_now_add=True)

    assigned_to = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks_assigned' 
    )
    created_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tasks_created'   
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # use auto_now for updates
    project_id = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )