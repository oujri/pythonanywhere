from django import forms
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class FormProfilInscription(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    confirmer_votre_mot_de_passe = forms.CharField(widget=forms.PasswordInput())
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('username','email','first_name','last_name','password')

    def clean(self):
        cleaned_data = super(FormProfilInscription, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirmer_votre_mot_de_passe")

        email = cleaned_data.get('email')
        username = cleaned_data.get('username')

        if email and User.objects.filter(email=email).exclude(username=username).exists():
            self.add_error('email', "Cet E-mail est déjà enregistré.")

        if password != confirm_password:
            self.add_error("password", "Les deux mot de passes ne sont pas identiques.")


class loginform(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['email', 'password']

class userform(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'email', 'first_name', 'last_name']


class userProfile(forms.ModelForm):
    class Meta:
        model = Profil
        exclude = ['last_logout', 'user']

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = '__all__'


class formConfirmEmail(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = '__all__'