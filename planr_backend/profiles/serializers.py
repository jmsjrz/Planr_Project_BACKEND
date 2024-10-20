from rest_framework import serializers
from .models import Interest, Profile

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class ProfileSerializer(serializers.ModelSerializer):
    interests_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Interest.objects.all(), write_only=True)  # Pour les centres d'intérêt

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'gender', 'birth_date', 'profile_image', 'bio', 'interests_ids', 'account_type']

    def update(self, instance, validated_data):
        interests = validated_data.pop('interests_ids', None)
        if interests:
            instance.interests.set(interests)

        profile = super().update(instance, validated_data)
        # Vérifier si le profil est complet après la mise à jour
        profile.check_profile_completion()
        return profile

