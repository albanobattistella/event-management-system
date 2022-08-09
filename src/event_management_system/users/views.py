from urllib import request
from django.http import HttpResponse, HttpResponseServerError, HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .authentication import get_user, handle_failed_authorization
from .models import Profile
from django.core import serializers
from django.contrib.auth.models import User, make_password, Group
from django.contrib.auth import authenticate, login, logout
from .forms import CreateForm, EditForm, LoginForm
from django.contrib.auth.decorators import login_required


def user_reset_password(request, user_id):
    if Profile.objects.filter(id=user_id).exists():
        user = User.objects.select_related('profile').filter(id=user_id)[0]      
        user.profile.reset_password()
        return HttpResponseRedirect(f"/users/edit/{user_id}?pwreset=success")

    return HttpResponse("User not found.")


def user_overview(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/users/login/")
    
    return render(request, "users/overview.html", {'users':User.objects.all().select_related('profile')})

def user_delete(request, user_id):
    if User.objects.filter(id=user_id).exists(): 
        User.objects.filter(id=user_id).delete() 
        print("Deleted")
    return HttpResponseRedirect("/users/")

def user_create(request):
    if request.method == 'POST':
        form = CreateForm(request.POST)
        if form.is_valid():
            user = User()
            user.username = request.POST['email']
            user.email = request.POST['email']
            user.last_name = request.POST['last_name']
            user.first_name = request.POST['first_name']
            user.password = make_password(request.POST['password'])
            user.save()

            # TODO: This should only be possible by admins
            if request.POST['user_role'] == 'CO':
                group = Group.objects.get(name='Contact')
                group.user_set.add(user)
            elif request.POST['user_role'] == 'AT':
                group = Group.objects.get(name='Attendant')
                group.user_set.add(user)
            elif request.POST['user_role'] == 'OR':
                group = Group.objects.get(name='Organisator')
                group.user_set.add(user)
            elif request.POST['user_role'] == 'AD':
                group = Group.objects.get(name='Administrator')
                group.user_set.add(user)


            profile = user.profile
            profile.website = request.POST['website']
            profile.company = request.POST['company']
            profile.over_18 = (request.POST.get('over_18', "off") == "on")
            profile.private_pin = request.POST['private_pin']
            profile.save()
            return HttpResponseRedirect('/users/')
    else:
        form = CreateForm()
        return render(request, 'users/create.html', {'form': form})

def user_edit(request, user_id):
    if request.method == 'POST':
        form = EditForm(request.POST)
        if form.is_valid():
            user = User.objects.select_related('profile').filter(id=user_id)[0]
            user.username = request.POST['email']
            user.email = request.POST['email']
            user.last_name = request.POST['last_name']
            user.first_name = request.POST['first_name']
            user.save()

            profile = user.profile
            profile.website = request.POST['website']
            profile.company = request.POST['company']
            profile.over_18 = (request.POST.get('over_18', "off") == "on")
            profile.private_pin = request.POST['private_pin']


            user.groups.clear()
            # TODO: This should only be possible by admins
            if request.POST['user_role'] == 'CO':
                group = Group.objects.get(name='Contact')
                group.user_set.add(user)
            elif request.POST['user_role'] == 'AT':
                group = Group.objects.get(name='Attendant')
                group.user_set.add(user)
            elif request.POST['user_role'] == 'OR':
                group = Group.objects.get(name='Organisator')
                group.user_set.add(user)
            elif request.POST['user_role'] == 'AD':
                group = Group.objects.get(name='Administrator')
                group.user_set.add(user)
            
            profile.save()
            return HttpResponseRedirect('/users/')
        return HttpResponseServerError()
    else:
        user = User.objects.select_related('profile').filter(id=user_id)[0]
        user_role = "CO"
        if user.groups.filter(name='Contact').exists():
            user_role = "CO"
        elif user.groups.filter(name='Attendant').exists():
            user_role = "AT"
        elif user.groups.filter(name='Organisator').exists():
            user_role = "OR"
        elif user.groups.filter(name='Administrator').exists():
            user_role = "AD"

        dict = {
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'password': user.password,
            'website': user.profile.website,
            'company': user.profile.company,
            'over_18': user.profile.over_18 == True,
            'private_pin': user.profile.private_pin,
            'user_role': user_role

        }

        pwreset = ""
        if 'pwreset' in request.GET:
            pwreset = request.GET['pwreset']

        form = EditForm(initial=dict)
        return render(request, 'users/edit.html', {'form': form, 'pwreset': pwreset})

def user_login(request):
    if request.method == 'POST':
        user = authenticate(username=request.POST['email'], password=request.POST['password'])
        if user.is_authenticated:
            login(request, user)
            return HttpResponseRedirect("/users/")
        else:
            form = LoginForm()
            return render(request, 'users/login.html', {'form': form, 'login_failed': True})
    else:
        if request.user is not None:
            form = LoginForm()
            return render(request, 'users/login.html', {'form': form, 'login_failed': False})

def user_logout(request):
    logout(request)
    return HttpResponseRedirect("/users/login/")