from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'modal-input',
            'placeholder': 'Enter username',
            'id': 'id_username'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'modal-input',
            'placeholder': 'Enter password',
            'id': 'id_password'
        })
    )

class SignupForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'modal-input',
            'placeholder': 'Enter email',
            'id': 'id_email'
        })
    )
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={
            'class': 'modal-input',
            'placeholder': 'Choose username',
            'id': 'id_username'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'modal-input',
            'placeholder': 'Choose password',
            'id': 'id_password'
        })
    )