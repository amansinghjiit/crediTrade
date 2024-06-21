import csv
import os
from pathlib import Path
from mimetypes import guess_type
from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .forms import PendingOrderForm
from .models import PendingOrder, DeliveredOrder, UserProfile, Transaction
from .utils import paginate_queryset, login_required_message, validate_size
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage

@login_required_message
def dashboard(request):
    if request.user.is_staff:
        recent_orders = DeliveredOrder.objects.all().order_by('-id')[:6]
        pending_orders = PendingOrder.objects.all().order_by('-id')[:6]
        amount_due = UserProfile.objects.aggregate(Sum('amount_due'))['amount_due__sum'] or Decimal('0.00')
        delivered_today_count = DeliveredOrder.objects.filter(date=timezone.now().date()).count()
        pending_orders_count = PendingOrder.objects.count()
        lifetime_orders_count = DeliveredOrder.objects.count()
        recent_transactions = Transaction.objects.all().order_by('-date', '-id')[:5]
        transaction_history = Transaction.objects.all().order_by('-date', '-id')
        
    else:
        user_profile = request.user.userprofile
        recent_orders = DeliveredOrder.objects.filter(user_profile=user_profile).order_by('-id')[:6]
        pending_orders = PendingOrder.objects.filter(user_profile=user_profile).order_by('-id')[:6]
        amount_due = user_profile.amount_due
        delivered_today_count = DeliveredOrder.objects.filter(user_profile=user_profile, date=timezone.now().date()).count()
        pending_orders_count = PendingOrder.objects.filter(user_profile=user_profile).count()
        lifetime_orders_count = DeliveredOrder.objects.filter(user_profile=user_profile).count()
        recent_transactions = Transaction.objects.filter(user_profile=user_profile).order_by('-date', '-id')[:5]
        transaction_history = Transaction.objects.filter(user_profile=user_profile).order_by('-date', '-id')
        
    return render(request, 'orders/dashboard.html', {
        'recent_orders': recent_orders,
        'amount_due': amount_due,
        'delivered_today_count': delivered_today_count,
        'lifetime_orders_count': lifetime_orders_count,
        'recent_transactions': recent_transactions,
        'transaction_history': transaction_history,
        'pending_orders': pending_orders,
        'pending_orders_count': pending_orders_count
    })

@login_required_message
def handle_form_submission(request, instance=None):
    form = PendingOrderForm(request.POST, instance=instance)
    if form.is_valid():
        pending_order = form.save(commit=False)
        pending_order.user_profile = request.user.userprofile
        pending_order.save()
        messages.success(request, "Form Submitted")
        return redirect('pending')
    else:
        messages.error(request, "Failed to submit. Please check your input")
        return render(request, 'orders/delivery_form.html', {'form': form})

@login_required_message
def delivery_form_view(request):
    if request.method == 'POST':
        return handle_form_submission(request)
    else:
        form = PendingOrderForm()
        pending_orders = PendingOrder.objects.all().order_by('-id')
        return render(request, 'orders/delivery_form.html', {'form': form, 'pending_orders': pending_orders})

@login_required_message
def pending_orders_view(request):
    if request.user.is_staff:
        pending_orders = PendingOrder.objects.all().order_by('-id')
    else:
        pending_orders = PendingOrder.objects.filter(user_profile=request.user.userprofile).order_by('-id')
    return render(request, 'orders/pending.html', {'pending_orders': pending_orders})

@login_required_message
def delete_entry(request, id):
    entry = get_object_or_404(PendingOrder, id=id)
    entry.delete()
    messages.success(request, "Order Deleted")
    return redirect('pending')

@login_required_message
def edit_entry(request, id):
    entry = get_object_or_404(PendingOrder, pk=id)
    if request.method == 'POST':
        return handle_form_submission(request, instance=entry)
    else:
        form = PendingOrderForm(instance=entry)
        return render(request, 'orders/delivery_form.html', {'form': form})

@login_required_message
def delivered_orders_view(request):
    if request.user.is_staff:
        delivered_orders = DeliveredOrder.objects.all().order_by('-id')
    else:
        delivered_orders = DeliveredOrder.objects.filter(user_profile=request.user.userprofile).order_by('-id')
    
    query = request.GET.get('q')
    if query:
        delivered_orders = delivered_orders.filter(
            Q(name__icontains=query) |
            Q(model__icontains=query) |
            Q(pin__icontains=query)
        )

    page_number = request.GET.get('page')
    delivered_orders_paginated, num_pages = paginate_queryset(delivered_orders, page_number)
    return render(request, 'orders/delivered.html', {'delivered_orders': delivered_orders_paginated, 'num_pages': num_pages, 'query': query})

@login_required_message
def upload_invoice(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(DeliveredOrder, pk=order_id)
        invoice = request.FILES.get('invoice')
        
        if not validate_size(invoice, request):
            return redirect('delivered')

        pin = order.pin.lower().replace(" ", "_")
        order_date = order.date
        y, m, d = order_date.year, order_date.strftime("%m"), order_date.strftime("%d")
        original_filename, original_extension = os.path.splitext(invoice.name)
        invoice_name = f"{order.name.replace(' ', '_')}_{order_id}{original_extension}"
        destination_dir = f'invoices/{pin}/{y}/{m}/{d}'
        destination_path = os.path.join(destination_dir, invoice_name)
        saved_path = default_storage.save(destination_path, invoice)
        order.invoice.name = saved_path
        order.save()
        messages.success(request, "Invoice Uploaded")
    return redirect('delivered')

@login_required_message
def remove_invoice(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        delivered_order = get_object_or_404(DeliveredOrder, id=order_id)
        if delivered_order.invoice:
            try:
                invoice_path = delivered_order.invoice.name
                default_storage.delete(invoice_path)
                delivered_order.invoice = None
                delivered_order.save()
                messages.success(request, 'Invoice Removed')
            except Exception as e:
                messages.error(request, f'Error deleting invoice: {e}')
        else:
            messages.error(request, 'No invoice found to remove')
    return redirect('delivered')

@login_required_message
def view_invoice(request, order_id):
    delivered_order = get_object_or_404(DeliveredOrder, id=order_id)
    if delivered_order.invoice:
        try:
            invoice_url = default_storage.url(delivered_order.invoice.name)
            response = redirect(invoice_url)
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(delivered_order.invoice.name)}"'
            return response
        except Exception as e:
            messages.error(request, f"Error retrieving invoice: {e}")
    else:
        messages.error(request, "Invoice not found")
    return redirect('delivered')

@login_required_message
def export_pending_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=pending_orders.csv'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Tracking', 'OTP', 'OBD', 'Model', 'Pin'])

    pending_orders = PendingOrder.objects.all()
    for order in pending_orders:
        writer.writerow([order.name, order.tracking, order.otp, order.obd, order.model, order.pin])
    return response

@login_required_message
def export_delivered_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=delivered_orders.csv'

    writer = csv.writer(response)
    writer.writerow(['User', 'Date', 'Name', 'Model', 'Pin', 'Invoice', 'Return'])

    delivered_orders = DeliveredOrder.objects.all().order_by('-id')
    for order in delivered_orders:
        formatted_date = order.date.strftime('%d %B')
        writer.writerow([
            order.user_profile.name,
            formatted_date,
            order.name,
            order.model,
            order.pin,
            '1' if order.invoice else '0',
            order.return_amount
        ])
    return response

@staff_member_required
def payments_dashboard(request):
    user_profiles = UserProfile.objects.all()
    return render(request, 'orders/payments_dashboard.html', {'user_profiles': user_profiles})

@staff_member_required
def user_payment_details(request, user_id):
    user_profile = get_object_or_404(UserProfile, id=user_id)
    return render(request, 'orders/payments_dashboard.html', {'user_profile': user_profile})

@staff_member_required
def make_payment(request, user_id):
    user_profile = get_object_or_404(UserProfile, id=user_id)
        
    if request.method == 'POST':
        date = request.POST.get('date')
        amount = request.POST.get('amount')
        transaction_type = request.POST.get('type')
        description = request.POST.get('description')
        
        Transaction.objects.create(
            user_profile=user_profile,
            date=date,
            amount=amount,
            transaction_type=transaction_type,
            description=description
        )
        
        return redirect('payments_dashboard')
    else:
        return render(request, 'orders/payments_dashboard.html', {'user_profile': user_profile})

@staff_member_required
def transaction_history(request, user_profile_id):
    user_profile = get_object_or_404(UserProfile, id=user_profile_id)
    user_transactions = Transaction.objects.filter(user_profile_id=user_profile_id).order_by('-date', '-id')
    return render(request, 'orders/payments_dashboard.html', {
        'user_profile': user_profile,
        'user_transactions': user_transactions
    })

@staff_member_required
def export_payment_details(request):
    user_profiles = UserProfile.objects.filter(amount_due__gt=0)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payment_details.csv"'
    response.write(u'\ufeff'.encode('utf8'))
    writer = csv.writer(response)
    writer.writerow(['User', 'A/C holder', 'A/C Number', 'IFSC', 'Due'])
    for user_profile in user_profiles:
        writer.writerow([
            user_profile.name,
            user_profile.account_holder_name,
            user_profile.account_number,
            user_profile.ifsc_code,
            user_profile.amount_due
        ])
    return response
