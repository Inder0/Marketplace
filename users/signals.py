from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Profile
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
            email_address=EmailAddress.objects.filter(user=instance, primary=True).first()
            if email_address is None:
                EmailAddress.objects.create(user=instance, email=instance.email, primary=True, verified=False)
            elif email_address.email != instance.email:
                email_address.email = instance.email
                email_address.verified = False
                email_address.save()
                try:
                    email_address.send_confirmation(request=None)
                except Exception:
                    pass