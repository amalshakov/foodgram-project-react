import re

from django.conf import settings
from django.forms import ValidationError


def validate_username(username):
    if username in settings.FORBIDDEN_USERNAMES:
        raise ValidationError(f'Использовать имя <{username}> запрещено')
    result = re.sub(r'[\w.@+-]+', '', username)
    if result:
        raise ValidationError(
            'Имя пользователя содержит недопустимые символы: '
            f'{result}'
        )
    return username
