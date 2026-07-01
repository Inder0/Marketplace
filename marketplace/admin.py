from django.contrib import admin
from .models import Product,Order,ProductImage
# Register your models here.

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(ProductImage)
