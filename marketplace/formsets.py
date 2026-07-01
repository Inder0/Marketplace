from django.forms import inlineformset_factory

from .models import Product, ProductImage


ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    fields=["image"],
    extra = 4,
    max_num = 5,
    validate_max = True,
    can_delete=True,
)