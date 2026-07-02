from django.forms import inlineformset_factory
from .forms import ProductImageForm
from .models import Product, ProductImage


ProductImageFormSet = inlineformset_factory(
    Product,
    ProductImage,
    form=ProductImageForm,
    fields=["image"],
    extra = 4,
    max_num = 5,
    validate_max = True,
    can_delete=True,
)