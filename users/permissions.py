from rest_framework.permissions import BasePermission



class IsRegister(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return bool(request.user)



