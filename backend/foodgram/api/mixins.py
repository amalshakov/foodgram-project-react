from users.validators import validate_username


class UsernameValidateMixin():

    def validate_username(self, value):
        return validate_username(value)
