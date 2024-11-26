from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required

# View for the homepage, displaying the login form
def home(request):
    """
    Renders the homepage, showing the authentication form to log in.
    
    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: The response with the 'signin.html' template and the authentication form.
    """
    if request.user.is_authenticated:
        # Si el usuario está autenticado, redirigir a la página de 'customers'
        return redirect('customers')  # Reemplaza 'customers' con el nombre de la URL que apunta a la vista de clientes.
    else:
        # Si el usuario no está autenticado, mostrar la página de inicio de sesión
        return render(request, "signin.html", {'form': AuthenticationForm()})

# View for user signup
def signup(request):
    """
    Handles new user registration. If the method is GET, the registration form is shown.
    If the method is POST, it tries to create a new user and authenticate them.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: Renders the signup page or redirects to 'customers' if the signup is successful.
    """
    if request.method == "GET":
        return render(request, "signup.html", {'form': UserCreationForm()})
    else:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()  # Saves the new user to the database
                login(request, user)  # Authenticates and logs in the user after registration
                return redirect('customers')
            except IntegrityError:  # Handles error if the username already exists
                return render(request, "signup.html", {
                    'form': form,
                    'error': "Username already exists"  # Shows an error if the username is already taken
                })
        else:
            return render(request, "signup.html", {
                'form': form,
                'error': form.errors  # Displays form errors if registration is invalid
            })

# View for user login
def signin(request):
    """
    Handles user login. If the method is GET, it shows the authentication form.
    If the method is POST, it authenticates the user based on the provided username and password.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: Redirects to 'customers' if authentication is successful or shows an error if it fails.
    """
    if request.method == 'GET':
        return render(request, "signin.html", {'form': AuthenticationForm})
    else:
        # Authenticates the user with the provided credentials
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            login(request, user)  # Logs in the user if credentials are correct
            return redirect('customers')
        else:
            return render(request, "signin.html", {
                'form': AuthenticationForm,
                'error': 'Username or password is incorrect'  # Displays error if credentials are wrong
            })

# View for user logout
@login_required
def closeSession(request):
    """
    Logs out the current user and redirects them to the homepage.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: Redirects to the 'home' page after logging out.
    """
    logout(request)  # Logs out the user
    return redirect("home")  # Redirects to the homepage
