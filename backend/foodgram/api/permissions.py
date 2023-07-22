from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    '''Разрешение на изменение - авторам рецепта.
    Остальные - только чтение.
    '''
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (request.user.is_authenticated and request.user == obj.author)
        )
