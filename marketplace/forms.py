from django import forms
from .models import Product, ProductImage,Review

class ProductForm(forms.ModelForm):
    class Meta:
        model=Product
        fields=['name','description','price','product_type','file']
        widgets={
            'name':forms.TextInput(attrs={'placeholder':'Name','class': 'form-input'}),
            'description':forms.Textarea(attrs={'class': 'form-input min-h-32','placeholder':'Add information about the product','rows':4}),
            'price':forms.NumberInput(attrs={'placeholder':'Price','class': 'form-input'}),
            'product_type':forms.Select(attrs={'class': 'form-input',"id": "id_product_type",}),

            'file':forms.FileInput(attrs={'accept':'*','class':  '''block w-full text-sm text-slate-300
                                                                    file:mr-4
                                                                    file:rounded-xl
                                                                    file:border-0
                                                                    file:bg-gray-200
                                                                    file:px-4
                                                                    file:py-2
                                                                    hover:file:bg-gray-300
                                                                    ''',"id": "id_file",}),
        }
        labels={
            'file':'Digital File',
            'product_type':'Product Type (Physical/Digital)',
        }
    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get("product_type")
        file = cleaned_data.get("file")
        if product_type == "digital" and not file:
            self.add_error(
                "file",
                "Digital products require a downloadable file."
            )

        return cleaned_data


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "review"]
        widgets = {
            "rating": forms.Select(
                choices=[(i, i) for i in range(1, 6)],
                attrs={"class":"form-input"}
            ),
            "review": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Share your thoughts about this product (optional)...",
                    "class":"form-input"

                }
            ),
        }
        
class CheckoutForm(forms.Form):
    shipping_name = forms.CharField(max_length=100)
    shipping_phone = forms.CharField(max_length=20)
    shipping_address_line_1 = forms.CharField(max_length=255)
    shipping_address_line_2 = forms.CharField(
        max_length=255,
        required=False,
    )
    shipping_city = forms.CharField(max_length=100)
    shipping_state = forms.CharField(max_length=100)
    shipping_postal_code = forms.CharField(max_length=20)
    shipping_country = forms.CharField(max_length=100)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-input"

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ["image"]

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if image and image.size > 5 * 1024 * 1024:
            raise forms.ValidationError(
                "Image size must be less than 5 MB."
            )

        return image