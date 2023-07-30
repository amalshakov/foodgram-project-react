from django.db import transaction
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User


class CreateUserSerializer(UserCreateSerializer):
    '''Сериализатор для создания пользователей.'''

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
            'id',
        )


class UserSerializer(DjoserUserSerializer):
    '''Сериализатор пользователей.'''
    is_subscribed = serializers.BooleanField(
        default=False, read_only=True, source='subscribed_exists'
    )

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )


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


class RecipeFollowUserField(serializers.Field):
    """Сериализатор для вывода рецептов в подписках."""

    def get_attribute(self, instance):
        request = self.context.get('request')
        recipes = Recipe.objects.filter(author=instance.author)
        if request:
            limit = request.GET.get('recipes_limit')
            if limit:
                return recipes[: int(limit)]
        return recipes

    def to_representation(self, recipes_list):
        recipes_data = []
        for recipes in recipes_list:
            recipes_data.append(
                {
                    "id": recipes.id,
                    "name": recipes.name,
                    "image": recipes.image.url,
                    "cooking_time": recipes.cooking_time,
                }
            )
        return recipes_data


class FollowSerializer(serializers.ModelSerializer):
    '''Сериализатор подписок.
    Для вывода авторов рецепта на которых подписан текущий пользователь.
    '''
    recipes = RecipeFollowUserField()
    recipes_count = serializers.SerializerMethodField(read_only=True)
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed',
                  'recipes', 'recipes_count')

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            user=obj.user, author=obj.author
        ).exists()


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
    id = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'amount',
        )


class RecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для получения рецепта/рецептов.'''
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = ReadIngredientInRecipeSerializer(
        many=True,
        source='ingredient_list',
        read_only=True,
    )
    image = Base64ImageField()
    is_favorited = serializers.BooleanField(
        default=False, read_only=True
    )
    is_in_shopping_cart = serializers.BooleanField(
        default=False, read_only=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    '''Сериализатор для создания рецепта.'''
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
            'author',
        )

    def create_ingredients(self, ingredients, recipe):
        ingredients_list = []
        for ingredient in ingredients:
            create_ingredients = IngredientInRecipe(
                recipe=recipe,
                ingredients_id=ingredient.get('id'),
                amount=ingredient.get('amount'),
            )
            ingredients_list.append(create_ingredients)
        IngredientInRecipe.objects.bulk_create(ingredients_list)

    def validate(self, data):
        """Проверка вводных данных при создании/редактировании рецепта.
        """
        ingredients = data.get('ingredients')
        ingredients_list = []
        for item in ingredients:
            if item['id'] in ingredients_list:
                raise serializers.ValidationError(
                    'Нельзя добавлять одинаковые ингредиенты!'
                )
            ingredients_list.append(item['id'])
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')
        data.update(
            {
                'tags': tags,
                'ingredients': ingredients,
                'author': self.context.get('request').user,
            }
        )
        return data

    @transaction.atomic
    def create(self, validated_data):
        '''Создает рецепт.'''
        tags_data = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        image = validated_data.pop('image')
        recipe = Recipe.objects.create(
            image=image,
            **validated_data
        )
        self.create_ingredients(ingredients_data, recipe)
        recipe.tags.set(tags_data)
        return recipe

    @transaction.atomic
    def update(self, recipe, validated_data):
        """Обновляет рецепт."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        author = recipe.author
        for key, value in validated_data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)
        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)
        if ingredients:
            recipe.ingredients.clear()
            self.create_ingredients(ingredients, recipe)
        recipe.author = author
        recipe.save()
        return recipe

    def to_representation(self, recipe):
        '''Для поддержки сериализации, для операций чтения.'''
        data = RecipeSerializer(
            recipe,
            context={'request': self.context.get('request')}
        ).data
        return data


class ShopListSerializer(serializers.ModelSerializer):
    """Серилизатор для списка покупок."""
    class Meta:
        fields = (
            'recipe', 'user'
        )
        model = ShoppingCart

    def validate(self, data):
        user = data['user']
        if user.shopping_cart_recipes.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в список покупок'
            )
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Серилизатор для избранных рецептов."""

    class Meta:
        fields = (
            'recipe', 'user'
        )
        model = Favorite

    def validate(self, data):
        user = data['user']
        if user.favorite_recipes.filter(recipe=data['recipe']).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        return data

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data
