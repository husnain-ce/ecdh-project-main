# serializers.py
from rest_framework import serializers
from .models import Patient, User


class PatientSerializer(serializers.ModelSerializer):
    # Add fields for the user's first name and last name
    user_first_name = serializers.ReadOnlyField(source='user.first_name')
    user_last_name = serializers.ReadOnlyField(source='user.last_name')
    user_id = serializers.ReadOnlyField(source='user.id')

    class Meta:
        model = Patient
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
