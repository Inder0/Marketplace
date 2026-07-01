from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.templatetags.static import static
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
import os


# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/', blank=True, null=True,)
    displayname = models.CharField(max_length=200, blank=True)
    info = models.TextField(null=True, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    address_line_1 = models.CharField(max_length=255, blank=True)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username
    
    @staticmethod
    def compress_image(image_field):
        img = Image.open(image_field)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        max_size = (800, 800)
        img.thumbnail(max_size)
        buffer = BytesIO()
        img.save(
            buffer,
            format="JPEG",
            quality=75,
            optimize=True
        )
        filename = os.path.splitext(
            image_field.name
        )[0] + ".jpg"
        return ContentFile(
            buffer.getvalue(),
            name=filename


        )
    def save(self, *args, **kwargs):
        compress=False
        if not self.pk:
            compress=True
        else:
            old_image = Profile.objects.get(pk=self.pk).image
            if old_image != self.image:
                compress=True
        if compress and self.image:
            self.image = self.compress_image(self.image)

        super().save(*args, **kwargs)
    
    @property
    def name(self):
        return self.displayname if self.displayname else self.user.username
    
    @property
    def avatar(self):
        if self.image:
            return self.image.url
        else:
            return static('images/default_avatar.png')