from django.contrib import admin
from django.contrib.admin import register
from users.models import Follow, User


@register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
    )
    empty_value_display = 'значение отсутствует'
    list_filter = ('username', 'email')


admin.site.register(Follow)
