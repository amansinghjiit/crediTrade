from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import PendingOrder, DeliveredOrder, Transaction
from django.db.models import Sum
from decimal import Decimal


@receiver(post_save, sender=PendingOrder)
def handle_pending_order_status(sender, instance, **kwargs):
    if instance.status == 'Delivered':
        DeliveredOrder.objects.create(
            user_profile=instance.user_profile,
            name=instance.name,
            model=instance.model,
            pin=instance.pin
        )
        instance.delete()


@receiver([post_save, post_delete], sender=DeliveredOrder)
def update_transaction(sender, instance, **kwargs):
    user_profile = instance.user_profile
    date = instance.date

    total_return_amount = DeliveredOrder.objects.filter(
        user_profile=user_profile,
        date=date,
        return_amount__isnull=False
    ).aggregate(total=Sum('return_amount'))['total'] or Decimal('0')

    if total_return_amount > 0:
        Transaction.objects.update_or_create(
            user_profile=user_profile,
            date=date,
            transaction_type='credit',
            defaults={
                'description': "Order Delivered",
                'amount': total_return_amount,
                'auto_created': True
            }
        )
    else:
        Transaction.objects.filter(
            user_profile=user_profile,
            date=date,
            transaction_type='credit',
            auto_created=True
        ).delete()


@receiver(pre_save, sender=Transaction)
def store_old_user_profile(sender, instance, **kwargs):
    if instance.pk:
        instance._old_user_profile = Transaction.objects.get(pk=instance.pk).user_profile
    else:
        instance._old_user_profile = None

@receiver([post_save, post_delete], sender=Transaction)
def update_amount_due(sender, instance, **kwargs):

    def recalc(user_profile):
        if not user_profile:
            return

        total_credit = Transaction.objects.filter(
            user_profile=user_profile,
            transaction_type='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        total_debit = Transaction.objects.filter(
            user_profile=user_profile,
            transaction_type='debit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        user_profile.amount_due = total_credit - total_debit
        user_profile.save(update_fields=['amount_due'])

    recalc(instance.user_profile)

    if hasattr(instance, '_old_user_profile'):
        recalc(instance._old_user_profile)
