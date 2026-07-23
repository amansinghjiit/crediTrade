import csv
import os
import re
import json
import requests
import logging
from decimal import Decimal
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from .forms import PendingOrderForm
from .models import PendingOrder, DeliveredOrder, UserProfile, Transaction
from .utils import paginate_queryset, login_required_message, validate_size
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from dotenv import load_dotenv
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
load_dotenv()


def _pending_orders_queryset(request):
    if request.user.is_staff:
        return PendingOrder.objects.all().order_by('-id')
    if request.user.username == 'sumeet2796':
        return PendingOrder.objects.filter(
            Q(user_profile=request.user.userprofile) |
            Q(pin__in=['Jagdamba 766015', 'Wholesale 492001', 'Pansari 767001'])
        ).order_by('-id')
    if request.user.username == 'mhetarashu':
        return PendingOrder.objects.filter(
            Q(user_profile=request.user.userprofile) | Q(pin='416118 / 416115')
        ).order_by('-id')
    if request.user.username == 'kr.somesh007':
        return PendingOrder.objects.filter(
            Q(user_profile=request.user.userprofile) | Q(pin='Delhi 110091')
        ).order_by('-id')
    if request.user.username == 'mohitnigam0778':
        return PendingOrder.objects.filter(
            Q(user_profile=request.user.userprofile) | Q(pin='274305/274306')
        ).order_by('-id')
    return PendingOrder.objects.filter(user_profile=request.user.userprofile).order_by('-id')


def _render_pending_partial(request, toast_message=None, toast_type='success'):
    response = render(request, 'partials/orders/pending.html', {
        'pending_orders': _pending_orders_queryset(request),
        'is_staff': request.user.is_staff,
    })
    response['HX-Push-Url'] = reverse('pending')
    if toast_message:
        response['HX-Trigger'] = json.dumps({
            'showToast': {'message': toast_message, 'type': toast_type}
        })
    return response

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
        
    else:
        user_profile = request.user.userprofile
        recent_orders = DeliveredOrder.objects.filter(user_profile=user_profile).order_by('-id')[:6]
        pending_orders = PendingOrder.objects.filter(user_profile=user_profile).order_by('-id')[:6]
        amount_due = user_profile.amount_due
        delivered_today_count = DeliveredOrder.objects.filter(user_profile=user_profile, date=timezone.now().date()).count()
        pending_orders_count = PendingOrder.objects.filter(user_profile=user_profile).count()
        lifetime_orders_count = DeliveredOrder.objects.filter(user_profile=user_profile).count()
        recent_transactions = Transaction.objects.filter(user_profile=user_profile).order_by('-date', '-id')[:5]

    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'partials/orders/dashboard.html' if is_htmx else 'orders/dashboard.html'
    return render(request, template, {
        'recent_orders': recent_orders,
        'amount_due': amount_due,
        'delivered_today_count': delivered_today_count,
        'lifetime_orders_count': lifetime_orders_count,
        'recent_transactions': recent_transactions,
        'pending_orders': pending_orders,
        'pending_orders_count': pending_orders_count
    })


@login_required_message
def dashboard_transactions(request):
    if request.user.is_staff:
        transactions = Transaction.objects.all().order_by('-date', '-id')[:100]
    else:
        transactions = Transaction.objects.filter(
            user_profile=request.user.userprofile
        ).order_by('-date', '-id')[:100]
    return render(request, 'partials/orders/transaction_history.html', {
        'transaction_history': transactions,
    })
    
# WhatsApp API credentials
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_NUMBER_ID')

@login_required_message
def handle_form_submission(request, instance=None):
    form = PendingOrderForm(request.POST, instance=instance)
    is_htmx = request.headers.get('HX-Request') == 'true'
    if form.is_valid():
        pending_order = form.save(commit=False)
        pending_order.user_profile = request.user.userprofile
        pending_order.save()

        pin_to_phone = {
            'Jagdamba 766015': '919437367463',
            'Wholesale 492001': '919078979263', 
            'Pansari 767001': '919078979263',
            'Delhi 110091': '917015194057', 
            '416118 / 416115': '918237084370',
            '274305'/'274306': '918181070148',
        }
        to_number = pin_to_phone.get(pending_order.pin, '917982405815')

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": f"{pending_order.name}\n{pending_order.tracking}\nOTP: {pending_order.otp}\nOBD: {pending_order.obd}\n{pending_order.model or 'N/A'}\nPin: {pending_order.pin}"
            }
        }

        try:
            logger.debug("Sending WhatsApp to %s", to_number)
            response = requests.post(
                f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"},
                data=json.dumps(payload)
            )
            if response.status_code == 200:
                logger.debug("WhatsApp sent to %s", to_number)
            else:
                logger.warning("WhatsApp failed to %s status=%s", to_number, response.status_code)
        except requests.exceptions.RequestException as e:
            logger.error("WhatsApp error to %s: %s", to_number, e)

        if is_htmx:
            return _render_pending_partial(request, 'Form Submitted')
        messages.success(request, "Form Submitted")
        return redirect('pending')
    else:
        if is_htmx:
            return render(request, 'partials/orders/delivery_form.html', {'form': form})
        messages.error(request, "Failed to submit. Please check your input")
        return render(request, 'orders/delivery_form.html', {'form': form})

@login_required_message
def delivery_form_view(request):
    if request.method == 'POST':
        return handle_form_submission(request)
    else:
        form = PendingOrderForm()
        is_htmx = request.headers.get('HX-Request') == 'true'
        template = 'partials/orders/delivery_form.html' if is_htmx else 'orders/delivery_form.html'
        return render(request, template, {'form': form})

@login_required_message
def pending_orders_view(request):
    pending_orders = _pending_orders_queryset(request)
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'partials/orders/pending.html' if is_htmx else 'orders/pending.html'
    return render(request, template, {'pending_orders': pending_orders, 'is_staff': request.user.is_staff})

@login_required_message
def delete_entry(request, id):
    entry = get_object_or_404(PendingOrder, id=id)
    entry.delete()
    is_htmx = request.headers.get('HX-Request') == 'true'
    if is_htmx:
        return _render_pending_partial(request, 'Order Deleted')
    messages.success(request, "Order Deleted")
    return redirect('pending')

@login_required_message
def edit_entry(request, id):
    entry = get_object_or_404(PendingOrder, pk=id)
    if request.method == 'POST':
        return handle_form_submission(request, instance=entry)
    else:
        form = PendingOrderForm(instance=entry)
        is_htmx = request.headers.get('HX-Request') == 'true'
        template = 'partials/orders/delivery_form.html' if is_htmx else 'orders/delivery_form.html'
        return render(request, template, {'form': form})

@login_required_message
def delivered_orders_view(request):
    if request.user.is_staff:
        delivered_orders = DeliveredOrder.objects.all().order_by('-id') 
    elif request.user.username == 'sumeet2796':
        delivered_orders = DeliveredOrder.objects.filter(Q(user_profile=request.user.userprofile) | Q(pin__in=['Jagdamba 766015','Wholesale 492001'])).order_by('-id')
    else:
        delivered_orders = DeliveredOrder.objects.filter(user_profile=request.user.userprofile).order_by('-id')
    
    query = request.GET.get('q')
    if query:
        delivered_orders = delivered_orders.filter(
            Q(name__istartswith=query) |
            Q(model__icontains=query) |
            Q(pin__icontains=query) |
            Q(tracking__icontains=query)
        )

    page_number = request.GET.get('page')
    delivered_orders_paginated, num_pages = paginate_queryset(delivered_orders, page_number, per_page=50)
    is_htmx = request.headers.get('HX-Request') == 'true'
    hx_target = request.headers.get('HX-Target', '')
    if is_htmx and hx_target == 'delivered-results':
        template = 'partials/orders/delivered_results.html'
    elif is_htmx:
        template = 'partials/orders/delivered.html'
    else:
        template = 'orders/delivered.html'
    return render(request, template, {
        'delivered_orders': delivered_orders_paginated,
        'num_pages': num_pages,
        'query': query or '',
    })
@login_required_message
def upload_invoice(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(DeliveredOrder, pk=order_id)
        invoice = request.FILES.get('invoice')
        if not validate_size(invoice, request):
            return redirect('delivered')
        pin = re.sub(r'[ /]+', '_', order.pin.lower())
        original_filename, original_extension = os.path.splitext(invoice.name)
        invoice_name = f"{order.name.replace(' ', '_')}_{order_id}{original_extension}"
        destination_dir = pin
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
            invoice_url = f'https://zuhirawsoerfaijwzsuf.supabase.co/storage/v1/object/public/creditrade/{delivered_order.invoice.name}'
            response = redirect(invoice_url)
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(delivered_order.invoice.name)}"'
            return response
        except Exception as e:
            messages.error(request, f"Error retrieving invoice: {e}")
    else:
        messages.error(request, "Invoice not found")

    return redirect('delivered')

@staff_member_required
def trackmatch(request):
    try:
        api_url = "https://trackmatch-production.up.railway.app/api/"
        response = requests.get(api_url, timeout=120)
        response.raise_for_status()
        scraped_data = response.json().get('data', [])

        pending_orders = PendingOrder.objects.filter(pin="Delhi 110091", status='Pending').order_by('-id')
        scraped_tracking_map = {item['tracking']: item for item in scraped_data}

        table_data = []

        for order in pending_orders:
            scraped_item = scraped_tracking_map.get(order.tracking)

            if scraped_item:
                raw_date = scraped_item['date']
                try:
                    dt = datetime.strptime(raw_date, "%b %d, %Y %I:%M:%S %p")
                    formatted_date = dt.strftime("%d %b")
                except ValueError:
                    formatted_date = raw_date

                table_data.append({
                    'tracking': order.tracking,
                    'name': order.name,
                    'model': order.model or "N/A",
                    'match': True,
                    'date': formatted_date,
                    'product_name': scraped_item['product_name'],
                    'price': scraped_item['price']
                })
            else:
                table_data.append({
                    'tracking': order.tracking,
                    'name': order.name,
                    'model': order.model or "N/A",
                    'match': False,
                    'date': "-"
                })

        missing_data = []
        five_days_ago = datetime.now() - timedelta(days=5)

        for item in scraped_data:
            if not PendingOrder.objects.filter(tracking=item['tracking']).exists():
                raw_date = item['date']
                try:
                    dt = datetime.strptime(raw_date, "%b %d, %Y %I:%M:%S %p")
                    formatted_date = dt.strftime("%d %b")
                    if dt >= five_days_ago:
                        missing_data.append({
                            'date': formatted_date,
                            'product_name': item['product_name'],
                            'tracking': item['tracking'],
                            'price': item['price']
                        })
                except ValueError:
                    missing_data.append({
                        'date': raw_date,
                        'product_name': item['product_name'],
                        'tracking': item['tracking'],
                        'price': item['price']
                    })

        context = {
            'table_data': table_data,
            'missing_data': missing_data,
        }
        is_htmx = request.headers.get('HX-Request') == 'true'
        template = 'partials/orders/trackmatch.html' if is_htmx else 'orders/trackmatch.html'
        return render(request, template, context)

    except requests.RequestException as e:
        logger.error(f"API request failed: {str(e)}", exc_info=True)
        is_htmx = request.headers.get('HX-Request') == 'true'
        template = 'partials/orders/trackmatch.html' if is_htmx else 'orders/trackmatch.html'
        return render(request, template, {'error': 'Failed to fetch data.'})
    except Exception as e:
        logger.error(f"Trackmatch error: {str(e)}", exc_info=True)
        is_htmx = request.headers.get('HX-Request') == 'true'
        template = 'partials/orders/trackmatch.html' if is_htmx else 'orders/trackmatch.html'
        return render(request, template, {'error': 'An unexpected error occurred.'})
    
@login_required_message
def export_pending_orders_csv(request):
    user_profile = request.user.userprofile
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=pending_orders.csv'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Tracking', 'OTP', 'OBD', 'Model', 'Pin'])
    if request.user.is_superuser:
        pending_orders = PendingOrder.objects.all()
    else:
        pending_orders = PendingOrder.objects.filter(user_profile=user_profile)
    for order in pending_orders:
        writer.writerow([order.name, order.tracking, order.otp, order.obd, order.model, order.pin])
    return response

@login_required_message
def export_delivered_orders_csv(request):
    user_profile = request.user.userprofile
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=delivered_orders.csv'
    writer = csv.writer(response)
    writer.writerow(['User', 'Date', 'Name', 'Model', 'Pin', 'Tracking', 'Return'])

    if request.user.is_superuser:
        delivered_orders = DeliveredOrder.objects.all().order_by('-id')[:100]
    else:
        delivered_orders = DeliveredOrder.objects.filter(user_profile=user_profile).order_by('-id')[:100]

    for order in delivered_orders:
        formatted_date = order.date.strftime('%d %B')
        writer.writerow([
            order.user_profile.name,
            formatted_date,
            order.name,
            order.model,
            order.pin,
            order.tracking,
            order.return_amount
        ])
    return response

def _payments_dashboard_profiles():
    """Non-zero due only — no transaction prefetch (history loads lazily)."""
    return (
        UserProfile.objects.exclude(amount_due=0)
        .order_by('name')
        .only(
            'id', 'name', 'amount_due',
            'phonepe_name', 'phonepe_number',
            'account_holder_name', 'account_number', 'ifsc_code',
        )
    )


@staff_member_required
def payments_dashboard(request):
    user_profiles = _payments_dashboard_profiles()
    is_htmx = request.headers.get('HX-Request') == 'true'
    template = 'partials/orders/payments_dashboard.html' if is_htmx else 'orders/payments_dashboard.html'
    return render(request, template, {'user_profiles': user_profiles})

@staff_member_required
def user_payment_details(request, user_id):
    user_profile = get_object_or_404(UserProfile, id=user_id)
    return render(request, 'orders/payments_dashboard.html', {'user_profile': user_profile})

@staff_member_required
def make_payment(request, user_id):
    user_profile = get_object_or_404(UserProfile, id=user_id)
    is_htmx = request.headers.get('HX-Request') == 'true'
        
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
            description=description,
            auto_created=False
        )

        if is_htmx:
            # Re-render from DB after signal recalc — no client-side amount math
            response = render(request, 'partials/orders/payments_dashboard.html', {
                'user_profiles': _payments_dashboard_profiles(),
            })
            response['HX-Trigger'] = json.dumps({
                'showToast': {'message': 'Payment recorded', 'type': 'success'}
            })
            return response
        
        return redirect('payments_dashboard')
    else:
        return render(request, 'orders/payments_dashboard.html', {'user_profile': user_profile})

@staff_member_required
def transaction_history(request, user_profile_id):
    get_object_or_404(UserProfile, id=user_profile_id)
    transactions = (
        Transaction.objects.filter(user_profile_id=user_profile_id)
        .order_by('-date', '-id')
        .only('id', 'date', 'description', 'amount', 'transaction_type', 'user_profile_id')
    )
    return render(request, 'partials/orders/payment_transactions.html', {
        'transactions': transactions,
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
