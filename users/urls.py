from django.urls import path
from .views import ProfileEditView, my_profile, profile,profile_settings,profile_emailchange, send_verification_email
from .forms import CustomPasswordResetForm,CustomSetPasswordForm
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('profile-edit/',ProfileEditView.as_view(),name="profile-edit"),
    path('onboarding/',ProfileEditView.as_view(),name="profile-onboarding"),
    path("you/", my_profile, name="profile"),
    path("@<str:username>/", profile, name="profile-detail"),
    path("settings/", profile_settings, name="profile-settings"),
    path("email-change/", profile_emailchange, name="profile-emailchange"),
    path("send-verification/", send_verification_email, name="send-verification"),
    path("password-reset/", auth_views.PasswordResetView.as_view(form_class=CustomPasswordResetForm), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(form_class=CustomSetPasswordForm), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
]

