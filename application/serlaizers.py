from rest_framework import serializers
from . import models
from Auth import serlaizers as sr
from post import serializer as psr
class application_serializer(serializers.ModelSerializer):
    student=sr.UserStudentSerializer(required=False,many=False)
    team=psr.team_serializer(required=False,many=True)
    class Meta:
        model = models.Application
        fields = '__all__'