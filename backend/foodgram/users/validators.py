import re

from django.forms import ValidationError

from foodgram.settings import NOT_USERNAME


def validate_username(username):
    if username in NOT_USERNAME:
        raise ValidationError('Использовать имя "{username}" запрещено')
    result = re.sub(r'[\w.@+-]+', '', username)
    if result:
        raise ValidationError(
            'Имя пользователя содержит недопустимые символы: '
            f'{result}'
        )
    return username
