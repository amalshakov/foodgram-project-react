from django.contrib import admin
from django.contrib.admin import register

from .models import Tag, Recipe, Ingredient, IngredientInRecipe, Favorite, ShoppingCart


class IngredientRecipeInLine(admin.TabularInline):
    model = Recipe.ingredients.through
    extra = 2


@register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'slug',)


@register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'ingredients', 'amount',)
    list_filter = ('recipe',)
    save_on_top = True


@register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit',)
    save_on_top = True


@register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author',)
    list_filter = ('name', 'author__username', 'tags__name')
    save_on_top = True
    inlines = (IngredientRecipeInLine, )


@register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('user',)
    save_on_top = True


@register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe',)
    list_filter = ('user',)
    save_on_top = True
