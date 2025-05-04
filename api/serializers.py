from rest_framework import serializers
from .models import Party, User, Preference, SuggestedDestination, Vote

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {
            'start_date': {'required': False, 'allow_null': True},
            'end_date':   {'required': False, 'allow_null': True},
        }
        
class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = '__all__'

    def create(self, validated_data):
        # Asegurar que user es una instancia
        user_id = validated_data.pop('user')
        user = User.objects.get(id=user_id)
        return Preference.objects.create(user=user, **validated_data)

class SuggestedDestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SuggestedDestination
        fields = '__all__'

class VoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vote
        fields = '__all__'
