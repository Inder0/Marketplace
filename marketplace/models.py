from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Product(models.Model):
    seller=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    description=models.TextField()
    price=models.FloatField()
    file=models.FileField(upload_to='uploads/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)

    
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