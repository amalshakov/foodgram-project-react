from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.request import Request
from djoser.views import UserViewSet as DjoserUserViewSet
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from users.models import User, Follow
from recipes.models import Tag, Ingredient
from serializers import CustomUserSerializer, FollowSerializer, TagSerializer, IngredientSerializer


class UserViewSet(DjoserUserViewSet):
    '''ViewSet для работы с пользователями.'''
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (AllowAny,)

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
    '''ViewSet возвращает список тегов или тег по его id.'''
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    pass


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    '''ViewSet для работы с моделью Ingredient'''
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
