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
    due_date = models.DateTimeField()

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
    updated_by=models.ForeignKey(
        Users,
         on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_updated'
    )
    updated_at = models.DateTimeField(auto_now=True) 
    project_id = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )