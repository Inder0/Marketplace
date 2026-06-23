from django import forms
from .models import Profile
from django.forms import ModelForm
from allauth.account.forms import LoginForm,SignupForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm,SetPasswordForm

class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].widget.attrs.update({
            "class": "w-full bg-gray-100 border border-gray-700 rounded-xl px-4 py-3 text-black",
            "placeholder": "Enter your email",
        })

    def clean_email(self):
        email = self.cleaned_data.get("email")
        users = User.objects.filter(email=email)
        if not users.exists():
            return email
        for user in users:
            if not user.has_usable_password():
                raise forms.ValidationError(
                    "This account uses Google login. Please sign in with Google.")
        return email
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
        
class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'New Password'})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm New Password'})
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-input",
            })

class ProfileForm(ModelForm):
    class Meta:
        model=Profile
        exclude=['user','onboarding_completed']
        widgets={
            'displayname':forms.TextInput(attrs={'placeholder':'Display Name','class': 'form-input'}),
            'info':forms.Textarea(attrs={'class': 'form-input min-h-32','placeholder':'Add information about yourself','rows':4}),
            'image':forms.FileInput(attrs={'accept':'image/*','class':  '''
                                                                                    block w-full text-sm text-slate-300
                                                                                    file:mr-4
                                                                                    file:rounded-lg
                                                                                    file:border-0
                                                                                    file:bg-gray-200
                                                                                    file:px-4
                                                                                    file:py-2
                                                                                    hover:file:bg-gray-300
                                                                                '''}),
        }

class CustomLoginForm(LoginForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["login"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Username or Email"
        })

        self.fields["password"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Password"
        })

class CustomSignupForm(SignupForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["username"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Username"
        })

        self.fields["email"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Email Address"
        })

        self.fields["password1"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Password"
        })

        self.fields["password2"].widget.attrs.update({
            "class": "form-input",
            "placeholder": "Confirm Password"
        })

class EmailForm(ModelForm):
    email=forms.EmailField(required=True)
    class Meta:
        model=User
        fields=['email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs.update({
            "class": "form-input !bg-gray-600 !mt-2 !pr-3",
            "placeholder": "Email Address"
        })