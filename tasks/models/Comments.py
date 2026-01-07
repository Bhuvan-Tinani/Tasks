from django.db import models

from tasks.models import Task
from tasks.models.Users import Users

class Comments(models.Model):
    comment=models.TextField()
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    task=models.ForeignKey(Task, on_delete=models.CASCADE)
    