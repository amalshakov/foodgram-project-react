from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from recipes.models import (Favorite, Ingredient, Recipe,
                            ShoppingCart, Tag)
from users.models import Follow, User
from .filters import RecipeFilter
from .pagination import PageLimitPagination
from .permissions import AuthorStaffOrReadOnly
from .serializers import (CreateRecipeSerializer, FavoriteSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeSerializer, ShopListSerializer, TagSerializer,
                          UserSerializer)
from .utils import add_recipe, del_recipe, get_file_shopping_cart


class UserViewSet(DjoserUserViewSet):
    '''ViewSet для работы с пользователями.'''
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageLimitPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = self.queryset.annotate(
                subscribed_exists=Exists(Follow.objects.filter(
                    user_id=self.request.user.id,
                    author_id=OuterRef('pk')
                ))
            ).prefetch_related('recipes')
        else:
            queryset = self.queryset.prefetch_related('recipes')
        return queryset

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
        serializer = FollowSerializer(
            pages, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        '''Подписаться на автора рецепта.'''
        follower = get_object_or_404(User, id=id)
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

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        '''Отписаться от автора рецепта.'''
        follower = get_object_or_404(User, id=id)
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
    pagination_class = PageLimitPagination
    permission_classes = (AuthorStaffOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = Recipe.objects.select_related(
            'author').prefetch_related('tags')
        favorited = self.request.query_params.get('is_favorited')
        shopping_cart = self.request.query_params.get('is_in_shopping_cart')
        author = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')
        if favorited:
            queryset = queryset.filter(favorite_users__user=self.request.user)
        if shopping_cart:
            queryset = queryset.filter(
                shopping_cart_users__user=self.request.user
            )
        if author:
            queryset = queryset.filter(author=author)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags).distinct()
        if self.request.user.is_authenticated:
            return queryset.annotate(
                favorite_exists=Exists(
                    queryset.filter(
                        favorite_users__user=self.request.user,
                        favorite_users__recipe=OuterRef('id'),
                    )
                ),
                shopping_exists=Exists(
                    queryset.filter(
                        shopping_cart_users__user=self.request.user,
                        shopping_cart_users__recipe=OuterRef('id'),
                    )
                ),
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RecipeSerializer
        return CreateRecipeSerializer

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, pk=None):
        '''Добавляет рецепт в избранное.'''
        return add_recipe(request, FavoriteSerializer, pk)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        '''Удаляет рецепт из избранного.'''
        return del_recipe(request, Favorite, pk)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, pk=None):
        '''Добавляет рецепт в список покупок.'''
        return add_recipe(request, ShopListSerializer, pk)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        '''Удаляет рецепт из списка покупок.'''
        return del_recipe(request, ShoppingCart, pk)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,)
    )
    def download_shopping_cart(self, request):
        '''Скачивает список покупок.'''
        return get_file_shopping_cart(request.user)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    '''ViewSet для работы с моделью Ingredient.'''
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('^name',)  # поиск с 'параметром поиска' - /?search=...
