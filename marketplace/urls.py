from django.urls import path
from .views import *


urlpatterns=[
    path('', HomeView.as_view(), name='home'),
    path('products/<pk>', ProductDetail.as_view(), name='product-detail'),
    path('create-order/<pk>', create_order, name='create-order'),
    path('verify-payment/', verify_payment, name='verify-payment'),
    path('payment-success/', payment_success, name='payment-success'),
    path('payment-failed/', payment_failed, name='payment-failed'),
    path('create-product/', ProductCreateView.as_view(), name='create-product'),
    path('update-product/<pk>', ProductUpdateView.as_view(), name='update-product'),
    path('delete-product/<pk>', ProductDeleteView.as_view(), name='delete-product'),
    path('dashboard/',DashboardView.as_view(),name='dashboard'),
    path('purchases/',PurchaseView.as_view(),name='my-purchase'),
    path('analytics/',AnalyticsView.as_view(),name='analytics'),
    path('products/<pk>/review/',ReviewCreateView.as_view(),name='create-review'),
    path('products/<pk>/review/edit/',ReviewUpdateView.as_view(),name='update-review'),
    path('products/<pk>/review/delete/',ReviewDeleteView.as_view(),name='delete-review')


]