from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.

class Product(models.Model):
    seller=models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    description=models.TextField()
    price=models.FloatField()
    PRODUCT_TYPES = (
        ("digital", "Digital"),
        ("physical", "Physical"),
    )
    product_type=models.CharField(max_length=10,choices=PRODUCT_TYPES,default="digital")
    file=models.FileField(upload_to='uploads/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
         ordering=["-created_at"]

    @property
    def primary_image(self):
        image = self.images.first()
        if image:
            return image.image.url
        return "/static/images/No_Image_Available.jpg"    

    @property
    def extension(self):
        if self.file:
            return self.file.name.split('.')[-1].lower()
        return ""
    
    @property
    def file_url(self):
            return self.file.url if self.file else None

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
    shipping_name = models.CharField(max_length=100,blank=True)
    shipping_phone = models.CharField(max_length=20,blank=True)
    shipping_address_line_1 = models.CharField(max_length=255,blank=True)
    shipping_address_line_2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100,blank=True)
    shipping_state = models.CharField(max_length=100,blank=True)
    shipping_postal_code = models.CharField(max_length=20,blank=True)
    shipping_country = models.CharField(max_length=100,blank=True)
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
    
class ProductImage(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='images')
    image=models.ImageField(upload_to="product_images/")
    created_at=models.DateTimeField(auto_now_add=True)
    
     