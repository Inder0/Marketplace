from django import forms
from .models import Product,Review

class ProductForm(forms.ModelForm):
    class Meta:
        model=Product
        fields=['name','description','price','file',]
        widgets={
            'name':forms.TextInput(attrs={'placeholder':'Name','class': 'form-input'}),
            'description':forms.Textarea(attrs={'class': 'form-input min-h-32','placeholder':'Add information about the product','rows':4}),
            'price':forms.NumberInput(attrs={'placeholder':'Price','class': 'form-input'}),
            'file':forms.FileInput(attrs={'accept':'*','class':  '''
                                                                                    block w-full text-sm text-slate-300
                                                                                    file:mr-4
                                                                                    file:rounded-xl
                                                                                    file:border-0
                                                                                    file:bg-gray-200
                                                                                    file:px-4
                                                                                    file:py-2
                                                                                    hover:file:bg-gray-300
                                                                                '''}),
        }


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
        