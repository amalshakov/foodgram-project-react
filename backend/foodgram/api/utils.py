from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response

from recipes.models import IngredientInRecipe, Recipe


def add_recipe(request, add_serializer, pk=None):
    """Добавляет рецепт."""
    recipe = get_object_or_404(Recipe, id=pk)
    context = {'request': request}
    data = {
        'user': request.user.id,
        'recipe': recipe.id
    }
    serializer = add_serializer(data=data, context=context)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def del_recipe(request, model, pk=None):
    """Удаляет рецепт."""
    recipe = get_object_or_404(Recipe, id=pk)
    user = request.user
    try:
        obj = model.objects.get(user=user, recipe=recipe)
    except model.DoesNotExist:
        raise serializers.ValidationError(
            'Невозможно удалить. Рецепт не был добавлен!'
        )
    else:
        obj.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


def get_file_shopping_cart(user):
    '''Отдает файл с покупками(ингредиентами).'''
    ingredients = IngredientInRecipe.objects.filter(
        recipe__shopping_cart_users__user=user
    ).values('ingredients__name', 'ingredients__measurement_unit'
             ).annotate(amount=Sum('amount'))
    data = ingredients.values_list(
        'ingredients__name',
        'ingredients__measurement_unit',
        'amount'
    )
    shopping_cart = 'Список покупок:\n'
    for name, measurement_unit, amount in data:
        shopping_cart += (f'{name} {amount} {measurement_unit}\n')
    return FileResponse(shopping_cart, content_type='text/plain')
