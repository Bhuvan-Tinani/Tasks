from django.db import models

class Users(models.Model):
    username=models.CharField(max_length=255,unique=True)
    password=models.CharField(max_length=255)
    email=models.EmailField(unique=True)
    full_name=models.CharField(max_length=255)
    role=models.CharField(max_length=10,choices=(('user','User'),('admin','Admin')),default='user')
    created_by=models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users'
    )
    created_at=models.DateTimeField(auto_now_add=True)
    note=models.CharField(max_length=100,blank=True,null=True)

    def set_creator_and_note(self, current_user):
        if self.created_by is None:
            self.created_by = current_user
            self.note = "self"
        else:
            self.note = "admin" or self.note

class Project(models.Model):
    title = models.CharField(max_length=255)
    detail = models.TextField()

    created_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'admin'},
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.created_by is None or self.created_by.role != 'admin':
            raise ValueError("Only an admin user can create a project.")
        super().save(*args, **kwargs)

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


class Project_Assigned_User(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        Users,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'admin'},
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
        if self.assigned_by is None or self.assigned_by.role != 'admin':
            raise ValueError("Only an admin user can assign a project to users.")
        super().save(*args, **kwargs)

class Comments(models.Model):
    comment=models.TextField()
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    task=models.ForeignKey(Task, on_delete=models.CASCADE)
    
class Role(models.Model):
    name=models.CharField(max_length=255)