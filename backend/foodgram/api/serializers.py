from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from users.models import User, Follow
from recipes.models import Recipe, Tag, Ingredient, IngredientInRecipe
from .mixins import UsernameValidateMixin


class CreateUserSerializer(UserCreateSerializer, UsernameValidateMixin):
    '''Сериализатор для создания пользователей.'''

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    '''Сериализатор пользователей.'''
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
        )

    def get_is_subscribed(self, obj: User) -> bool:
        '''Проверка подписки пользователя на автора рецепта.'''
        user = self.context.get('request').user
        if user.is_anonymous or user == obj:
            return False
        return user.follower.filter(author=obj).exists()


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    '''Минифицированный сериализатор для рецептов.'''

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = ('__all__',)


class FollowSerializer(serializers.ModelSerializer):
    '''Сериализатор подписок.
    Для вывода авторов рецепта на которых подписан текущий пользователь.
    '''
    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers. SerializerMethodField()
    recipes = RecipeMinifiedSerializer(many=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )
        read_only_fields = ('__all__',)

    def get_is_subscribed(self, obj: User) -> bool:
        '''Проверка подписки пользователя на автора рецепта.'''
        return True

    def get_recipes_count(self, obj: User) -> int:
        '''Показывает общее количество рецептов автора
        на которого подписан текущий пользователь.
        '''
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    '''Сериализатор для Тегов.'''

    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug',
        )

#  1, 4


class IngredientSerializer(serializers.ModelSerializer):
    '''Сериализатор для получения ингредиента
    или получения списка ингредиентов.
    '''

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class ReadIngredientInRecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для вывода информации об ингредиенте в рецепте.'''
    id = serializers.ReadOnlyField(source='ingredients.id')
    name = serializers.ReadOnlyField(source='ingredients.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredients.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount',
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для выбора ингредиента при создании рецепта.'''

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'amount',
        )
