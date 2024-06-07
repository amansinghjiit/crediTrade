from django.contrib import messages
from django.shortcuts import redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from functools import wraps

def validate_size(value, request):
    min_size = 50 * 1024  # 50 KB
    max_size = 5 * 1024 * 1024  # 5 MB
    if value.size < min_size:
        messages.error(request, f'The file size ({value.size}) is below the minimum allowed size of 50 KB.')
        return False
    elif value.size > max_size:
        messages.error(request, f'The file size ({value.size}) exceeds the maximum allowed size of 5 MB.')
        return False
    return True

def login_required_message(function):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please login to continue.")
            return redirect('home')
        return function(request, *args, **kwargs)
    return wrapper

def paginate_queryset(queryset, page_number, per_page=50):
    paginator = Paginator(queryset, per_page)
    try:
        paginated_queryset = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_queryset = paginator.page(1)
    except EmptyPage:
        paginated_queryset = paginator.page(paginator.num_pages)
    return paginated_queryset, paginator.num_pages
