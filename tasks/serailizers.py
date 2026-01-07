from rest_framework import serializers

from tasks.models.Project import Project

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model=Project
        fields=['id','title','detail','created_at','created_by']