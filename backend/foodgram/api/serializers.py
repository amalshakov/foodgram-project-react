from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, validators
from drf_extra_fields.fields import Base64ImageField
from django.db.models import QuerySet, F

from users.models import User, Follow
from recipes.models import Recipe, Tag, Ingredient, IngredientInRecipe, ShoppingCart, Favorite
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


class RecipeFollowUserField(serializers.Field):
    """Сериализатор для вывода рецептов в подписках."""

    def get_attribute(self, instance):
        return Recipe.objects.filter(author=instance.author)

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
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()


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
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

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

    @staticmethod
    def get_ingredients(obj: Recipe) -> QuerySet[dict]:
        '''Получает список ингредиентов для рецепта.'''
        ingredients = IngredientInRecipe.objects.filter(recipe=obj)
        return ReadIngredientInRecipeSerializer(ingredients, many=True).data

    def get_is_favorited(self, obj: Recipe) -> bool:
        '''Проверяет находится ли рецепт в избанном.'''
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.favorite_recipes.filter(recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        '''Проверяет находится ли рецепт в списке покупок.'''
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart_recipes.filter(recipe=obj).exists()


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

    @staticmethod
    def create_ingredients(
        ingredients: QuerySet[list], recipe: Recipe
    ) -> None:
        '''Создает или обновляет записи в модели IngredientInRecipe для
        указанного рецепта и списка ингредиентов.
        Создает ингредиенты для рецепта.
        '''
        for ingredient in ingredients:
            amount = ingredient['amount']
            if IngredientInRecipe.objects.filter(
                    recipe=recipe,
                    ingredients=get_object_or_404(
                        Ingredient, id=ingredient['id'])).exists():
                amount += F('amount')
            IngredientInRecipe.objects.update_or_create(
                recipe=recipe,
                ingredients=get_object_or_404(
                    Ingredient, id=ingredient['id']),
                defaults={'amount': amount})

    def validate(self, data):
        """Проверка вводных данных при создании/редактировании рецепта.
        """
        tags = self.initial_data.get("tags")
        ingredients = self.initial_data.get("ingredients")

        data.update(
            {
                "tags": tags,
                "ingredients": ingredients,
                "author": self.context.get("request").user,
            }
        )
        return data

    def create(self, validated_data: dict) -> Recipe:
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

    def update(self, recipe: Recipe, validated_data: dict):
        """Обновляет рецепт.

        Args:
            recipe (Recipe): Рецепт для изменения.
            validated_data (dict): Изменённые данные.

        Returns:
            Recipe: Обновлённый рецепт.
        """
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")

        for key, value in validated_data.items():
            if hasattr(recipe, key):
                setattr(recipe, key, value)

        if tags:
            recipe.tags.clear()
            recipe.tags.set(tags)

        if ingredients:
            recipe.ingredients.clear()
            self.create_ingredients(ingredients, recipe)

        recipe.save()
        return recipe

    def to_representation(self, recipe: Recipe) -> Recipe:
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
                'Рецепт уже добавлен в корзину'
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
