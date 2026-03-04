from rest_framework import serializers
from .models import Electeur

class ElecteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Electeur
        fields = '__all__'