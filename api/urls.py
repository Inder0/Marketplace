from rest_framework.routers import DefaultRouter, path
from .views import CheckoutView, OrderViewSet, ProductViewSet, ProfileView, ReviewViewSet,PaymentVerificationView,AnalyticsView,PublicProfileView


app_name = 'api'
router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('reviews', ReviewViewSet, basename='review')
router.register('orders', OrderViewSet, basename='order')

urlpatterns = router.urls
urlpatterns += [
    path('checkout/', CheckoutView.as_view(), name='checkout'), 
    path('payments/verify/', PaymentVerificationView.as_view(), name='verify-payment'),
    path('dashboard/analytics/', AnalyticsView.as_view(), name='analytics'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/<str:username>/', PublicProfileView.as_view(), name='public-profile'),
]