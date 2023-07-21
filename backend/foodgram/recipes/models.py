from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint

from foodgram.settings import (MAX_AMOUNT_INGREDIENT, MAX_COOKING_TIME,
                               MIN_AMOUNT_INGREDIENT, MIN_COOKING_TIME)
from users.models import User
from .validators import validate_slug


class Tag(models.Model):
    '''Теги для рецептов.'''
    name = models.CharField(
        'Название тега',
        max_length=200,
        unique=True,
    )
    color = models.CharField(
        'Цвет в HEX',
        max_length=7,
        null=True,
    )
    slug = models.CharField(
        'Уникальный слаг',
        max_length=200,
        unique=True,
        null=True,
        validators=(validate_slug,),
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('slug',)

    def __str__(self):
        return f'{self.name} - {self.slug}'


class Recipe(models.Model):
    '''Рецепты'''
    tags = models.ManyToManyField(
        verbose_name='Тег рецепта',
        related_name='recipes',
        to=Tag,
    )
    author = models.ForeignKey(
        verbose_name='Автор рецепта',
        related_name='recipes',
        to=User,
        on_delete=models.CASCADE,
    )
    ingredients = models.ManyToManyField(
        verbose_name='Ингредиенты для приготовления блюда',
        related_name='recipes',
        to='Ingredient',
        through='IngredientInRecipe',
    )
    name = models.CharField(
        'Название блюда',
        max_length=200,
    )
    image = models.ImageField(
        'Фото блюда',
        upload_to='recipes/',
        blank=True,
        null=True,
        help_text='Загрузите фото блюда',
    )
    text = models.TextField(
        'Описание блюда',
        help_text='Введите полное описание блюда',
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления в минутах',
        help_text='Введите время приготовления блюда, в минутах',
        validators=(
            MaxValueValidator(
                MAX_COOKING_TIME, 'Слишком большое время приготовления блюда'
            ),
            MinValueValidator(
                MIN_COOKING_TIME, 'Недопустимое время приготовления блюда'
            ),
        ),
    )
    pub_date = models.DateTimeField(
        'Дата создания рецепта',
        auto_now_add=True,
        editable=False,
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    '''Ингредиенты для рецепта.'''
    name = models.CharField(
        'Название ингредиента',
        max_length=200,
    )
    measurement_unit = models.CharField(
        'Единица измерения ингредиента',
        max_length=200,
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self) -> str:
        return self.name


class IngredientInRecipe(models.Model):
    '''Таблица связывает модель Recipe и модель Ingredient
    с указанием количества игредиента.
    '''
    recipe = models.ForeignKey(
        to=Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_list'
    )
    ingredients = models.ForeignKey(
        to=Ingredient,
        on_delete=models.CASCADE,
    )
    amount = models.PositiveSmallIntegerField(
        'Количество ингредиента',
        help_text='Введите количество ингредиента',
        validators=(
            MinValueValidator(
                MIN_AMOUNT_INGREDIENT, 'Некорректное количество ингредиента'
            ),
            MaxValueValidator(
                MAX_AMOUNT_INGREDIENT, 'Очень большое количество ингредиента'
            ),
        ),
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            UniqueConstraint(
                fields=['recipe', 'ingredients'],
                name='unique_ingredient_in_recipe',
            ),
        ]

    def __str__(self):
        return f'{self.amount}'


class Favorite(models.Model):
    '''Избранные рецепты пользователя.
    Связывает модель Recipe и модель User.
    '''
    user = models.ForeignKey(
        verbose_name='Пользователь, который добавил рецепт в избранное',
        related_name='favorite_recipes',
        to=User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        verbose_name='Рецепт, который пользователь добавил в избранное',
        related_name='favorite_users',
        to=Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite',
            ),
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'


class ShoppingCart(models.Model):
    '''Список покупок.
    Связывает модель Recipe и модель User.
    '''
    user = models.ForeignKey(
        verbose_name='Пользователь, добавляющий рецепт в список покупок',
        related_name='shopping_cart_recipes',
        to=User,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        verbose_name='Рецепт, добавляемый пользователем в список покупок',
        related_name='shopping_cart_users',
        to=Recipe,
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart',
            ),
        ]

    def __str__(self):
        return f'{self.user} добавил в список покупок {self.recipe}'
