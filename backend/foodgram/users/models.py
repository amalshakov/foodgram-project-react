from django.db import models
from django.db.models import F, Q, CheckConstraint, UniqueConstraint
from django.contrib.auth.models import AbstractUser

from foodgram.settings import EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH
from .validators import validate_username


class User(AbstractUser):
    '''Модель пользователя.'''
    email = models.EmailField(
        'email',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=(validate_username,),
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
    )
    password = models.CharField(
        'Пароль',
        max_length=150,
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self) -> str:
        return f'{self.username}'


class Follow(models.Model):
    '''Подписки пользователя на авторов рецепта.'''
    user = models.ForeignKey(
        verbose_name='Подписчик',
        related_name='follower',
        to=User,
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        verbose_name='Автор рецепта',
        related_name='following',
        to=User,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow',
            ),
            CheckConstraint(
                check=~Q(author=F('user')),
                name='no_self_follow'
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user.username} -> {self.author.username}'
