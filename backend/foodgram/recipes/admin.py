from django.contrib import admin

from recipes.models import Tag, Recipe, Ingredient, IngredientInRecipe, Favorite, ShoppingCart


admin.site.register(Tag)
admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(IngredientInRecipe)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)
