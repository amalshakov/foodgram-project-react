from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Recipe


class RecipeFilter(FilterSet):
    """"Фильтр для сортировки рецептов."""""
    tags = filters.AllValuesMultipleFilter(
        field_name='tags__slug',
        label='tags'
    )
    is_favorited = filters.BooleanFilter(method='get_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'author',
            'tags',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, queryset, name, value):
        if value:
            return queryset.filter(favorite_users__user=self.request.user)
        return queryset.exclude(favorite_users__user=self.request.user)

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value:
            return queryset.filter(
                shopping_cart_users__user=self.request.user
            )
        return queryset


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'
