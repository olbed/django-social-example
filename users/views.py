from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from actions.models import Action
from actions.utils import create_action
from common.decorators import ajax_required
from .forms import UserEditForm, ProfileEditForm
from .models import Contact


@login_required
def dashboard(request):
    actions = Action.objects.exclude(user=request.user)
    following_ids = request.user.following.values_list('id', flat=True)

    if following_ids:
        actions = actions.filter(user_id__in=following_ids)
    actions = actions.select_related('user', 'user__profile').prefetch_related('target')[:15]

    ctx = dict(section='dashboard', actions=actions)
    return render(request, 'users/dashboard.html', ctx)


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile,
                                       data=request.POST,
                                       files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('dashboard')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    ctx = dict(user_form=user_form, profile_form=profile_form)
    return render(request, 'users/edit.html', ctx)


@login_required
def user_list(request):
    users = User.objects.filter(is_active=True)
    ctx = dict(section='people', users=users)
    return render(request, 'users/user/list.html', ctx)


@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    ctx = dict(section='people', user=user)
    return render(request, 'users/user/detail.html', ctx)


@ajax_required
@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            contact_user = User.objects.get(id=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user, user_to=contact_user)
                create_action(request.user, 'is following', contact_user)
            else:
                Contact.objects.filter(user_from=request.user, user_to=contact_user).delete()
            return JsonResponse({'status': 'ok'})
        except User.DoesNotExist:
            pass
    return JsonResponse({'status': 'error'})
