import random
import string
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponseForbidden

from .forms import StudentRegistrationForm
from .models import Student

def collect_errors_as_messages(request, form):
    for field, errors in form.errors.items():
        for error in errors:
            if field == '__all__':
                messages.error(request, f"{error}")
            else:
                label = form.fields[field].label or field.replace('_', ' ').title()
                messages.error(request, f"{label}: {error}")
                
                
def register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful! Please log in.")
            return redirect('login')
        else:
            collect_errors_as_messages(request, form)
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=identifier, password=password)

        if user is None:
            try:
                found = Student.objects.get(email__iexact=identifier)
                user = authenticate(request, username=found.username, password=password)
            except Student.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username/email or password.")

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')
    return render(request, 'accounts/dashboard.html', {'student': request.user})

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")
    students = Student.objects.filter(is_superuser=False).order_by('-date_joined')
    return render(request, 'accounts/admin_dashboard.html', {'students': students})

@login_required
def admin_register_student(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Not allowed")

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Student registered successfully.")
            return redirect('admin_dashboard')
        else:
            collect_errors_as_messages(request, form)
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/admin_register.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = Student.objects.get(email__iexact=email)
        except Student.DoesNotExist:
            messages.error(request, "No account found with that email.")
            return render(request, 'accounts/forgot_password.html')

        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        user.reset_code = code
        user.reset_code_expires = timezone.now() + timedelta(hours=2)
        user.save()
        
        try:
            send_mail(
                subject='Kamcoder - Password Reset Code',
                message=(
                    f'Hello {user.full_name},\n\n'
                    f'Your password reset code is: {code}\n\n'
                    f'This code expires in 2 hours.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            messages.success(request, "A 5-character code has been sent to your email.")
        except Exception as e:
            messages.error(request, f"Could not send email: {e}")
            return render(request, 'accounts/forgot_password.html')

        request.session['reset_email'] = user.email
        return redirect('verify_code')

    return render(request, 'accounts/forgot_password.html')


def verify_code(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')

    if request.method == 'POST':
        entered = request.POST.get('code', '').strip().upper()
        try:
            user = Student.objects.get(email=email)
        except Student.DoesNotExist:
            messages.error(request, "Something went wrong.")
            return redirect('forgot_password')

        if (user.reset_code == entered and
                user.reset_code_expires and
                user.reset_code_expires > timezone.now()):
            request.session['reset_verified'] = True
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid or expired code.")

    return render(request, 'accounts/verify_code.html')


def reset_password(request):
    email = request.session.get('reset_email')
    verified = request.session.get('reset_verified')
    if not email or not verified:
        return redirect('forgot_password')

    if request.method == 'POST':
        p1 = request.POST.get('password1', '')
        p2 = request.POST.get('password2', '')

        if p1 != p2:
            messages.error(request, "Passwords do not match.")
        elif len(p1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        else:
            user = Student.objects.get(email=email)
            user.set_password(p1)
            user.reset_code = ''
            user.reset_code_expires = None
            user.save()

            request.session.pop('reset_email', None)
            request.session.pop('reset_verified', None)

            messages.success(request, "Password reset successful. Please log in.")
            return redirect('login')

    return render(request, 'accounts/reset_password.html')

