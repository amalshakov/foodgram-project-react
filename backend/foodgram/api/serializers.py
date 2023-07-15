from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from django.db.models import QuerySet, F

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
    recipes = RecipeMinifiedSerializer(many=True, read_only=True)
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')

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
        return Recipe.objects.filter(author=obj.author).count()


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


class RecipeSerializerInCartInFavorite(serializers.ModelSerializer):
    '''Сериализатор для вывода рецептов в списке покупок и избранном.'''

    class Meta:
        model = Recipe
        fiels = (
            'id',
            'name',
            'image',
            'cooking_time'
        )

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
