# inventory/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # First user (superuser) gets admin role automatically
        role = 'admin' if instance.is_superuser else 'customer'
        UserProfile.objects.create(user=instance, role=role)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        role = 'admin' if instance.is_superuser else 'customer'
        UserProfile.objects.create(user=instance, role=role)