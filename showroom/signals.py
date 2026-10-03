from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Expense, Order, Purchase, Sale
from .automation import sync_expense, sync_order, sync_purchase, sync_sale


@receiver(post_save, sender=Sale)
def sale_saved(sender, instance, **kwargs):
    sync_sale(instance)


@receiver(post_delete, sender=Sale)
def sale_deleted(sender, instance, **kwargs):
    sync_sale(instance, is_delete=True)


@receiver(post_save, sender=Purchase)
def purchase_saved(sender, instance, **kwargs):
    sync_purchase(instance)


@receiver(post_delete, sender=Purchase)
def purchase_deleted(sender, instance, **kwargs):
    sync_purchase(instance, is_delete=True)


@receiver(post_save, sender=Order)
def order_saved(sender, instance, **kwargs):
    sync_order(instance)


@receiver(post_save, sender=Expense)
def expense_saved(sender, instance, **kwargs):
    sync_expense(instance)


@receiver(post_delete, sender=Expense)
def expense_deleted(sender, instance, **kwargs):
    sync_expense(instance, is_delete=True)
