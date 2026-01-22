import os
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from orders.utils import login_required_message
from django.contrib.auth.views import PasswordResetConfirmView
from .forms import CustomSetPasswordForm
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from dotenv import load_dotenv
from accounts.models import UserProfile

load_dotenv()

def home(request):
    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        context = {
            'user_profile': user_profile,
            'is_authenticated': True
        }
    else:
        context = {
            'user_profile': {
                'name': 'User',
                'whatsapp_number': '7982405815'
            },
            'is_authenticated': False
        }
    return render(request, 'core/home.html', context)

def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        username = email.split('@')[0] 
        password = request.POST.get('password')
        key = request.POST.get('key')

        if key != '1212':
            messages.error(request, 'Invalid key')
        else:
            try:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.is_active = False
                user.save()
                send_verification_email(request, user)
                messages.success(request, 'Account created successfully. Please check your email to activate your account.')
                return redirect('home')
            except IntegrityError:
                messages.error(request, 'Email address already exists')

    return redirect('home')

def send_verification_email(request, user):
    subject = 'Activate your account'
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    domain = request.get_host()
    activation_link = f"https://{domain}{reverse_lazy('activate', kwargs={'uidb64': uid, 'token': token})}"
    message = (
        f"Hi {user.username},\n\n"
        "Please click the link below to activate your account:\n\n"
        f"{activation_link}\n\n"
        "Thank you,\n"
        "CrediTrade Team"
    )
    user.email_user(subject, message)

def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated. You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        return redirect('home')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email').lower()
        username = email.split('@')[0] 
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        ip_address = request.META.get('REMOTE_ADDR', None)
        
        if user is not None:
            auth_login(request, user)
            user.userprofile.last_login_ip = ip_address
            user.userprofile.save()
            messages.success(request, 'Login successful')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password')
            return redirect('home')

    if request.user.is_authenticated:
        return redirect('dashboard')

    return redirect('home')

def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
        messages.success(request, 'Logout successful')

    return redirect('home')

@login_required_message
def profile(request):
    user_profile = request.user.userprofile
    
    if request.method == 'POST':
        user_profile.name = request.POST.get('name', '')
        user_profile.email = request.POST.get('email', '')
        user_profile.whatsapp_number = request.POST.get('whatsapp', '')
        user_profile.account_holder_name = request.POST.get('accountHolderName', '')
        user_profile.account_number = request.POST.get('accountNumber', '')
        user_profile.ifsc_code = request.POST.get('ifscCode', '')
        user_profile.phonepe_name = request.POST.get('phonepeName', '')
        user_profile.phonepe_number = request.POST.get('phonepeNumber', '')   

        user_profile.save()
        messages.success(request, 'Changes Saved')

    return render(request, 'accounts/profile.html', {'user_profile': user_profile})

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, 'Password changed successfully')
        return super().form_valid(form)
