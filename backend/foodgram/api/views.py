from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import serializers
from rest_framework.filters import SearchFilter
from djoser.views import UserViewSet as DjoserUserViewSet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from django.http import HttpResponse

from users.models import User, Follow
from recipes.models import Tag, Ingredient, Recipe, Favorite, ShoppingCart, IngredientInRecipe
from .serializers import CustomUserSerializer, FollowSerializer, TagSerializer, IngredientSerializer, RecipeSerializer, CreateRecipeSerializer, RecipeMinifiedSerializer, ShopListSerializer, FavoriteSerializer
from .pagination import PageLimitPagination
from .permissions import AuthorStaffOrReadOnly
from .filters import RecipeFilter, IngredientSearchFilter


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
    def subscriptions(self, request):
        '''Возвращает пользователей, на которых подписан текущий пользователь.
        В выдачу добавляются рецепты.
        '''
        following = Follow.objects.filter(user=self.request.user)
        pages = self.paginate_queryset(following)
        serializer = FollowSerializer(pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id):
        '''Подписаться или отписаться от автора рецепта.'''
        follower = get_object_or_404(User, id=id)
        if request.method == 'POST':
            if self.request.user == follower:
                return Response({'message': 'Нельзя подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)
            if self.request.user.follower.filter(author=follower).exists():
                return Response({'message': 'Подписка уже есть'},
                                status=status.HTTP_400_BAD_REQUEST)
            follow = Follow.objects.get_or_create(user=self.request.user,
                                                author=follower)
            serializer = FollowSerializer(follow[0])
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if self.request.user.follower.filter(author=follower).exists():
            Follow.objects.filter(user=self.request.user,
                                author=follower).delete()
            return Response({'message': 'Вы успешно отписаны'},
                            status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Подписки и так нет'},
                        status=status.HTTP_400_BAD_REQUEST)


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

    # def perform_create(self, serializer):
    #     return serializer.save(author=self.request.user)

    # def perform_update(self, serializer):
    #     return serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk):
        '''Добавляет или удаляет рецепт из избранного.'''
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            context = {"request": request}
            data = {
                'user': request.user.id,
                'recipe': recipe.id
            }
            serializer = FavoriteSerializer(data=data, context=context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        user = request.user
        if user.favorite_recipes.filter(recipe=recipe).exists():
            get_object_or_404(
                Favorite,
                user=request.user.id,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise serializers.ValidationError('Нет рецепта для удаления из избранного.')

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk):
        '''Добавляет или удаляет рецепт из списка покупок.'''
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            context = {'request': request}
            data = {
                'user': request.user.id,
                'recipe': recipe.id
            }
            serializer = ShopListSerializer(data=data, context=context)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        user = request.user
        if user.shopping_cart_recipes.filter(recipe=recipe).exists():
            get_object_or_404(
                ShoppingCart,
                user=request.user.id,
                recipe=recipe
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        raise serializers.ValidationError('Нет рецепта для удаления из списка покупок.')

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
            shopping_cart += (f'{name} {amount} {measurement_unit}\n')
        return HttpResponse(shopping_cart, content_type='text/plain')


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    '''ViewSet для работы с моделью Ingredient.'''
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)
