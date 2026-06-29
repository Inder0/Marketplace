from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.

class Product(models.Model):
    seller=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    description=models.TextField()
    price=models.FloatField()
    file=models.FileField(upload_to='uploads/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
         ordering=["-created_at"]

    
    @property
    def extension(self):
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return ""
    
    @property
    def file_url(self):
            return self.file.url if self.file and self.file.name.split('.')[-1].lower() in '.jpg,.jpeg,.png,.gif,.webp,.heif' else '/static/images/No_Image_Available.jpg'

    @property
    def file_name(self):
        if self.file:
            return self.file.name.split('/')[-1]
        
        return ""


    def __str__(self):
        return self.name
    
class Order(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    amount=models.FloatField()
    razorpay_order_id=models.CharField(max_length=255,blank=True,null=True)
    razorpay_payment_id=models.CharField(max_length=100,blank=True,null=True)
    paid=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


class Review(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='reviews')
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='reviews')
    rating=models.PositiveSmallIntegerField(validators=[MinValueValidator(1),MaxValueValidator(5)])
    review=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints=[models.UniqueConstraint(
            fields=["product","user"],
            name="unique_product_review",
        )]

    def __str__(self):
        return f"{self.user} - {self.product} ({self.rating}/5)"
    
     