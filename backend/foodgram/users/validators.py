import re

from django.forms import ValidationError

from foodgram.settings import FORBIDDEN_USERNAMES


def validate_username(username):
    if username in FORBIDDEN_USERNAMES:
        raise ValidationError('Использовать имя "{username}" запрещено')
    result = re.sub(r'[\w.@+-]+', '', username)
    if result:
        raise ValidationError(
            'Имя пользователя содержит недопустимые символы: '
            f'{result}'
        )
    return username
