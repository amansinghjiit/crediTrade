from django.shortcuts import render
from orders.models import DeliveredOrder
from django.db.models import Q
from django.utils.dateparse import parse_date
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Max  
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required

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
    
    paginator = Paginator(orders, 100)
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
