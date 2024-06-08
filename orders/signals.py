from django.db.models.signals import post_save, post_delete
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
    ).aggregate(total_return_amount=Sum('return_amount'))['total_return_amount'] or Decimal('0')

    if total_return_amount > 0:
        Transaction.objects.update_or_create(
            user_profile=user_profile,
            date=date,
            transaction_type='credit',
            defaults={'description': "Order Delivered", 'amount': total_return_amount, 'auto_created': True}
        )
    else:
        Transaction.objects.filter(user_profile=user_profile, date=date, transaction_type='credit', auto_created=True).delete()

@receiver([post_save, post_delete], sender=Transaction)
def update_amount_due(sender, instance, **kwargs):
    user_profile = instance.user_profile
    total_credit = Transaction.objects.filter(user_profile=user_profile, transaction_type='credit').aggregate(total_credit=Sum('amount'))['total_credit'] or Decimal('0')
    total_debit = Transaction.objects.filter(user_profile=user_profile, transaction_type='debit').aggregate(total_debit=Sum('amount'))['total_debit'] or Decimal('0')
    user_profile.amount_due = total_credit - total_debit
    user_profile.save()
