from rest_framework.permissions import BasePermission,SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    owner_field = 'user'
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, self.owner_field) == request.user
    
class IsSellerOrReadOnly(IsOwnerOrReadOnly):
    owner_field = 'seller'
