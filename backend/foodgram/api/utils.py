from django.db.models import Sum
from django.http import FileResponse

from recipes.models import IngredientInRecipe


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
