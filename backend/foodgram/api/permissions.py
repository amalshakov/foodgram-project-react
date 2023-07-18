from rest_framework.permissions import SAFE_METHODS, BasePermission


class AuthorStaffOrReadOnly(BasePermission):
    '''Разрешение на изменение - авторам рецепта и служебного персонала.
    Остальные - только чтение.
    '''
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or (request.user.is_authenticated
                and (request.user.is_staff
                     or request.user == obj.author))
        )
