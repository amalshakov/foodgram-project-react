import csv
from io import StringIO

from django.db.models import Sum
from django.http import HttpResponse

from recipes.models import IngredientInRecipe


def get_file_shopping_cart(user):
    '''Отдает файл с покупками(ингредиентами).'''
    ingredients = (
        IngredientInRecipe
        .objects
        .filter(recipe__shopping_cart_users__user=user)
        .values('ingredients__name', 'ingredients__measurement_unit')
        .annotate(amount=Sum('amount'))
    )
    data = ingredients.values_list(
        'ingredients__name',
        'ingredients__measurement_unit',
        'amount'
    )
    file = StringIO()
    writer = csv.writer(file)
    writer.writerow(
        ['Название ингредиента', 'Единица измерения', 'Количество']
    )
    for name, measurement_unit, amount in data:
        writer.writerow([name, measurement_unit, amount])
    file.seek(0)
    response = HttpResponse(file, content_type='text/plain')
    response[
        'Content-Disposition'] = 'attachment; filename="shopping_cart.txt"'
    return response
