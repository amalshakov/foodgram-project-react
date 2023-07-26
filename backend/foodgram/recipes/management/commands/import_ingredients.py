import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


def process_file(name: str):
    return csv.reader(open(os.path.join(
        settings.BASE_DIR, 'recipes/data/', name
        ), 'r', encoding='utf-8'), delimiter=',')


class Command(BaseCommand):

    def handle(self, *args, **options):

        # парсер ингредиентов
        csv = process_file('ingredients.csv')
        next(csv, None)
        for row in csv:
            obj, created = Ingredient.objects.get_or_create(
                name=row[0],
                measurement_unit=row[1]
            )
        print('парсер категорий прошел успешно')
