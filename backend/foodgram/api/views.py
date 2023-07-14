from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.request import Request
from djoser.views import UserViewSet as DjoserUserViewSet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse

from users.models import User, Follow
from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, IngredientInRecipe
from .serializers import CustomUserSerializer, FollowSerializer, TagSerializer, IngredientSerializer, RecipeSerializer, CreateRecipeSerializer, RecipeMinifiedSerializer
from .pagination import PageLimitPagination
from .permissions import AuthorStaffOrReadOnly
from .filters import RecipeFilter


class UserViewSet(DjoserUserViewSet):
    '''ViewSet для работы с пользователями.'''
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageLimitPagination

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request: Request) -> Response:
        '''Возвращает пользователей, на которых подписан текущий пользователь.
        В выдачу добавляются рецепты.
        '''
        following = Follow.objects.filter(user=self.request.user)
        pages = self.paginate_queryset(following)
        serializer = FollowSerializer(pages, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request: Request, id: int = None) -> Response:
        '''Подписаться или отписаться от автора рецепта.'''
        user = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            serializer = FollowSerializer(
                author,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Follow.objects.create(user=user, author=author)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Follow.objects.delete(user=user, author=author)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    '''ViewSet для работы с моделью Tag.'''
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    '''ViewSet для работы с моделью Recipe.'''
    queryset = Recipe.objects.all()
    pagination_class = PageLimitPagination
    permission_classes = (AuthorStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return CreateRecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        return serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        '''Добавляет или удаляет рецепт из избранного.'''
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        get_object_or_404(Favorite, user=request.user, recipe=recipe).delete()
        return Response(
            {'message': 'Рецепт удален из избранного.'},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        '''Добавляет или удаляет рецепт из списка покупок.'''
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(recipe)
            return Response(
                data=serializer.data,
                status=status.HTTP_201_CREATED
            )
        get_object_or_404(
            ShoppingCart, user=request.user, recipe=recipe
        ).delete()
        return Response(
            {'message': 'Рецепт удален из списка покупок.'},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        '''Скачивает список покупок.'''
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart_users__user=user
        ).values('ingredients__name', 'ingredients__measurement_unit').annotate(
            amount=Sum('amount'))
        data = ingredients.values_list(
            'ingredients__name',
            'ingredients__measurement_unit',
            'amount',
        )
        shopping_cart = 'Список покупок:\n'
        for name, measurement_unit, amount in data:
            shopping_cart += (f'{name} {amount} {measurement_unit}')
        return HttpResponse(shopping_cart, content_type='text/plain')


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    '''ViewSet для работы с моделью Ingredient.'''
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
