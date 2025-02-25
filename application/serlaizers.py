from rest_framework import serializers
from . import models
from Auth import serlaizers as sr
from post import serializer as psr
class application_serializer(serializers.ModelSerializer):
    team=psr.team_serializer(read_only=True,many=False)
    proposal=serializers.CharField(required=True)
    status=serializers.CharField(read_only=True)
    approve=serializers.BooleanField(read_only=True)
    class Meta:
        model = models.Application
        fields = ['id','team','proposal','status','approve','atachedfile','links']