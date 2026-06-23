from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile
from .forms import EmailForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress
# Create your views here.
def profile(request,username=None):
    if username:
        profile=get_object_or_404(Profile,user__username=username)
    else:
        if not request.user.is_authenticated:
            return redirect("account_login")
        try:
            profile=request.user.profile
        except Profile.DoesNotExist:
            return redirect("account_login")
    return render(request,'users/profile.html',{'profile':profile})

@login_required
def my_profile(request):
    profile=Profile.objects.get_or_create(user=request.user)[0]
    return render(request,"users/profile.html",{"profile": profile})

class ProfileEditView(LoginRequiredMixin, UpdateView):
    form_class=ProfileForm
    template_name='users/partials/edit_profile.html'
    success_url = reverse_lazy("profile")

    def dispatch(self, request, *args, **kwargs):
        if (
            request.resolver_match.url_name == "profile-onboarding" 
            and request.user.profile.onboarding_completed
        ):
            return redirect("profile")
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        if self.request.htmx:
            return ["users/partials/edit_profile.html"]
        return ["users/onboarding.html"]
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["onboarding"] = self.request.resolver_match.url_name == "profile-onboarding"
        return context

    def get_object(self, queryset=None):
        return self.request.user.profile
    
    def form_valid(self, form):
        profile = form.save(commit=False)
        if self.request.resolver_match.url_name=="profile-onboarding":
            profile.onboarding_completed = True 
        profile.save()
        print(
            "SAVED:",
            profile.onboarding_completed
        )
        messages.success(self.request, "Profile updated successfully.")
        if self.request.htmx:
            response = HttpResponse()
            response["HX-Refresh"] = "true"
            return response
        
        return redirect("profile")
@login_required
def profile_settings(request):
    email_address = EmailAddress.objects.filter(user=request.user,primary=True).first()
    return render(request,"users/profile_settings.html",{"email_address":email_address})
@login_required
def profile_emailchange(request):
    if request.htmx:
        form=EmailForm(instance=request.user)
        return render(request,'users/partials/email_form.html',{'form':form})
    
    if request.method=="POST":
        form=EmailForm(request.POST,instance=request.user)
        if form.is_valid():
            email=form.cleaned_data.get("email")
            if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                messages.error(request,"This email address is already in use.")
                return redirect('profile-settings')
            form.save()
            messages.success(request,"Email address updated successfully.")
            return redirect('profile-settings')
        else:
            messages.error(request,"Please enter a valid email address.")
            return redirect('profile-settings')

    return redirect('home')

@login_required
def send_verification_email(request):
    email_address=request.user.emailaddress_set.filter(primary=True).first()
    if email_address and not email_address.verified:
        email_address.send_confirmation(request)
        messages.success(request,"Verification email sent.")
        
    response=HttpResponse()
    response["HX-Refresh"]="true"
    return response