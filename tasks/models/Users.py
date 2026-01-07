from django.db import models

from tasks.models.Role import Role


class Users(models.Model):
    username=models.CharField(max_length=255,unique=True)
    password=models.CharField(max_length=255)
    email=models.EmailField(unique=True)
    full_name=models.CharField(max_length=255)
    role=models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
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