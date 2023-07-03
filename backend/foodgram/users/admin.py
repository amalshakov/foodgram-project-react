from django.contrib import admin

from users.models import User, Follow


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


admin.site.register(User, UserAdmin)
admin.site.register(Follow)
