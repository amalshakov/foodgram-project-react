import re

from django.forms import ValidationError


def validate_slug(slug):
    result = re.sub(r'[-a-zA-Z0-9_]+', '', slug)
    if result:
        raise ValidationError(
            'Слаг содержит недопустимые символы: '
            f'{result}'
        )
    return slug
