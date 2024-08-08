from rest_framework.permissions import BasePermission


class LoginRequired(BasePermission):
    def has_permission(self, request, view):
        if (request.user.is_anonymous) or (request.auth is None):
            return False
        result = True if request.user.email == request.auth.payload.get('email') else False
        return bool(result and request.user.role_id)

class AdminRequired(BasePermission):
    def has_permission(self, request, view):
        result = False
        if (request.user.is_anonymous) or (request.auth is None):
            return result
        elif request.user.email == request.auth.payload.get('email'):
            result = True if (request.user.is_admin and request.user.role_id == 1 ) else False
        return result