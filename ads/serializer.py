from rest_framework import serializers

from ads.models import Category, Ad, Like


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class AdListSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    username = serializers.CharField()

    class Meta:
        model = Ad
        fields = ['id', 'name', 'username', 'price']


class AdDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    name_category = serializers.CharField()
    username = serializers.CharField()

    class Meta:
        model = Ad
        fields = ["id", "name", "username", "price", "description", "is_published", "name_category"]


class LikeSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )

    class Meta:
        model = Like
        fields = ['user', 'created']

    def create(self, validated_data):
        likes = Like.objects.create(**validated_data)
        likes.save()
        return likes
