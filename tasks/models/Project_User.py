from django.db import models

from tasks.models.Project import Project
from tasks.models.Users import Users


class Project_User(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects_assigned_by'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'user'], name='unique_project_user')
        ]
        verbose_name = "Project Assigned User"
        verbose_name_plural = "Project Assigned Users"

    def save(self, *args, **kwargs):
        if self.assigned_by is None or self.assigned_by.role.name != 'admin':
            raise ValueError("Only an admin user can assign a project to users.")
        super().save(*args, **kwargs)