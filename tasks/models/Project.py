from django.db import models

from tasks.models.Users import Users

class Project(models.Model):
    title = models.CharField(max_length=255)
    detail = models.TextField()

    created_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        print(self.created_by)
        if self.created_by is None or self.created_by.role.name != 'admin':
            raise ValueError("Only an admin user can create a project.")
        super().save(*args, **kwargs)