from django.shortcuts import render
from accounts.models import UserProfile
from orders.models import DeliveredOrder,Transaction
from django.db.models import Q,Sum
from django.utils.dateparse import parse_date
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Max  
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from io import BytesIO
from django.http import HttpResponse
from .pdf_utils import generate_pdf
from datetime import datetime
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.db.models import Count

@staff_member_required
def order_insights(request):
    date_range = request.GET.get("date_range", "").strip()
    selected_model = request.GET.get("model", "all")
    selected_pin = request.GET.get("pin", "all")
    selected_user = request.GET.get("user", "all")
    page_number = request.GET.get("page", 1)

    filters = Q()

    if date_range:
        dates = date_range.split(" to ")
        start_date = parse_date(dates[0].strip()) if dates[0] else None
        end_date = parse_date(dates[1].strip()) if len(dates) > 1 else None

        if start_date and end_date and start_date != end_date:
            filters &= Q(date__range=(start_date, end_date))
        elif start_date:
            filters &= Q(date=start_date)

    if selected_model != "all":
        filters &= Q(model=selected_model)

    if selected_pin != "all":
        filters &= Q(pin=selected_pin)

    users = DeliveredOrder.objects.values_list(
        "user_profile__name", "user_profile__whatsapp_number", "user_profile__user__username"
    ).distinct()

    user_options = []
    username_map = {}

    for name, whatsapp, username in users:
        display_value = ""
        
        if name and whatsapp:
            display_value = f"{name} - {whatsapp}"
        elif name:
            display_value = name
        elif whatsapp:
            display_value = f"{username} - {whatsapp}"
        else:
            display_value = username  

        user_options.append(display_value)
        username_map[display_value] = username  

    if selected_user != "all":
        username = username_map.get(selected_user)
        if username:
            filters &= Q(user_profile__user__username=username)

    orders = (
        DeliveredOrder.objects
        .select_related("user_profile")
        .only("date", "user_profile__name", "user_profile__whatsapp_number", "model", "return_amount", "pin")
        .filter(filters)
        .order_by('-date')
    )
    
    paginator = Paginator(orders, 50)
    page_obj = paginator.get_page(page_number)

    models = DeliveredOrder.objects.values('model').annotate(latest_date=Max('date')).order_by('-latest_date').values_list('model', flat=True)
    pins = DeliveredOrder.objects.values('pin').annotate(latest_date=Max('date')).order_by('-latest_date').values_list('pin', flat=True)

    return render(request, "analytics/order_insights.html", {
        "orders": page_obj,
        "models": models,
        "pins": pins,
        "users": user_options,
        "selected_model": selected_model,
        "selected_pin": selected_pin,
        "selected_user": selected_user,
        "selected_date_range": date_range,
    })
    
@staff_member_required   
def update_return_amount(request):
    if request.method == "POST":
        selected_orders_raw = request.POST.get("selected_orders", "").strip()
        return_amount = request.POST.get("return_amount", "").strip()
        
        if not selected_orders_raw:
            messages.error(request, "No rows selected!")
            return redirect(request.META.get('HTTP_REFERER'))

        selected_orders = [order_id for order_id in selected_orders_raw.split(",") if order_id.isdigit()]
        
        if not selected_orders:
            messages.error(request, "No rows selected!")
            return redirect(request.META.get('HTTP_REFERER'))
        
        if len(selected_orders) > 99:
            messages.error(request, "Can't update more than 99 rows!")
            return redirect(request.META.get('HTTP_REFERER'))

        if not return_amount.isdigit():
            messages.error(request, "Invalid return amount!")
            return redirect(request.META.get('HTTP_REFERER'))

        return_amount = int(return_amount)

        orders = DeliveredOrder.objects.filter(id__in=selected_orders)
        updated_rows = 0 

        for order in orders:
            order.return_amount = return_amount
            order.save()
            updated_rows += 1

        if updated_rows == 1:
            messages.success(request, "1 row updated!")
        else:
            messages.success(request, f"{updated_rows} rows updated!")
    
    return redirect(request.META.get('HTTP_REFERER'))

@staff_member_required
def ledger(request):
    date_range = request.GET.get("date_range", "").strip()
    selected_user = request.GET.get("user", "all")
    selected_description = request.GET.get("description", "all")
    page_number = request.GET.get("page", 1)
    export_pdf = request.GET.get("export_pdf", False)

    transaction_filters = Q()
    order_filters = Q()
    start_date, end_date = None, None

    if date_range:
        dates = date_range.split(" to ")
        try:
            start_date = datetime.strptime(dates[0].strip(), "%Y-%m-%d").date() if dates[0] else None
            end_date = datetime.strptime(dates[1].strip(), "%Y-%m-%d").date() if len(dates) > 1 and dates[1] else None
        except ValueError:
            start_date, end_date = None, None  

        if start_date and end_date:
            transaction_filters &= Q(date__range=(start_date, end_date))
            order_filters &= Q(date__range=(start_date, end_date))
        elif start_date:
            transaction_filters &= Q(date=start_date)
            order_filters &= Q(date=start_date)

    users = (
        UserProfile.objects.annotate(latest_transaction=Max("transaction__date"))
        .order_by("-latest_transaction")
        .values_list("name", "whatsapp_number", "user__username")
    )

    user_options = []
    username_map = {}

    for name, whatsapp, username in users:
        display_value = f"{name} - {whatsapp}" if name and whatsapp else name or whatsapp or username
        user_options.append(display_value)
        username_map[display_value] = username  

    if selected_user != "all":
        username = username_map.get(selected_user)
        if username:
            transaction_filters &= Q(user_profile__user__username=username)
            order_filters &= Q(user_profile__user__username=username)
            
    if selected_description != "all":
        transaction_filters &= Q(description=selected_description)

    user_filter = Q(user_profile__user__username=username) if selected_user != "all" else Q()
    past_transactions = Transaction.objects.filter(user_filter & Q(date__lt=start_date)) if start_date else Transaction.objects.none()
    total_debit_before = int(past_transactions.filter(transaction_type="debit").aggregate(Sum("amount"))["amount__sum"] or 0)
    total_credit_before = int(past_transactions.filter(transaction_type="credit").aggregate(Sum("amount"))["amount__sum"] or 0)
    opening_balance = int(total_credit_before - total_debit_before)

    transactions_chronological = Transaction.objects.filter(transaction_filters).order_by("date", "id")
    total_debit = int(transactions_chronological.filter(transaction_type="debit").aggregate(Sum("amount"))["amount__sum"] or 0)
    total_credit = int(transactions_chronological.filter(transaction_type="credit").aggregate(Sum("amount"))["amount__sum"] or 0)

    balance = opening_balance
    for transaction in transactions_chronological:
        amount = int(transaction.amount)
        if transaction.transaction_type == "credit":
            balance += amount
            transaction.credit = amount
            transaction.debit = 0
        elif transaction.transaction_type == "debit":
            balance -= amount
            transaction.debit = amount
            transaction.credit = 0
        transaction.balance = balance

    closing_balance = balance

    transactions = list(transactions_chronological)[::-1]

    if selected_user != "all":
        username = username_map.get(selected_user)
        if username:
            user_profile = UserProfile.objects.filter(user__username=username).first()
            display_name = user_profile.name if user_profile and user_profile.name else username
            whatsapp_number = user_profile.whatsapp_number if user_profile and user_profile.whatsapp_number else None
        else:
            display_name = "Unknown"
            whatsapp_number = None
    else:
        display_name = "All Users"
        whatsapp_number = None

    orders = DeliveredOrder.objects.filter(order_filters).order_by("-date", "-id")

    if export_pdf:
        buffer = BytesIO()
        generate_pdf(
            transactions, 
            opening_balance, 
            closing_balance, 
            total_debit, 
            total_credit, 
            display_name,
            whatsapp_number,
            start_date, 
            end_date, 
            orders,
            buffer
        )
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        if selected_user != "all" and username:
            response['Content-Disposition'] = f'attachment; filename="{username}_statement.pdf"'
        else:
            response['Content-Disposition'] = 'attachment; filename="all_statement.pdf"'
        return response
  
    paginator = Paginator(transactions, 50)
    page_obj = paginator.get_page(page_number)
    
    description_options = [
        "Bank Transfer",
        "UPI",
        "CC Payment",
        "CDM",
        "BULK",
        "Order Delivered",
    ]

    context = {
        "transactions": page_obj,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
        "user_options": user_options,
        "selected_user": selected_user,
        "selected_date_range": date_range,
        "description_options": description_options,
        "selected_description": selected_description, 
    }

    return render(request, "analytics/ledger.html", context)

@staff_member_required
def email_broadcast(request):
    users_with_orders = User.objects.filter(is_active=True).annotate(order_count=Count('userprofile__deliveredorder'))
    all_users_count, less_than_five_orders_count = users_with_orders.count(), users_with_orders.filter(order_count__lt=5).count()
    thresholds = [(t, users_with_orders.filter(order_count__gte=t).count()) for t in range(5, 51, 5)]

    if request.method == 'POST':
        subject, message_content, min_orders = request.POST.get('subject', ''), request.POST.get('message_content', ''), request.POST.get('min_orders', 'all')

        if not message_content:
            messages.error(request, 'Message cannot be empty')
            return redirect('email_broadcast')

        users = (
            users_with_orders if min_orders == 'all'
            else users_with_orders.filter(order_count__lt=5) if min_orders == 'less_than_5'
            else users_with_orders.filter(order_count__gte=int(min_orders))
        )
        
        email_list = [user.email for user in users]

        from_email = 'CrediTrade <noreply@creditrade.in>'
        email_messages = [
            EmailMessage(subject=subject, body=message_content, from_email=from_email, to=[user.email], reply_to=['noreply@creditrade.in'])
            for user in users
        ]
        
        try:
            [email.send(fail_silently=False) for email in email_messages]
            messages.success(request, f'Successfully sent to {len(email_list)} users')
        except Exception as e:
            messages.error(request, f'Error sending mail: {str(e)}')

        return redirect('email_broadcast')

    return render(request, 'analytics/email_broadcast.html', {
        'all_users_count': all_users_count,
        'less_than_five_orders_count': less_than_five_orders_count,
        'thresholds': thresholds
    })