from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from PIL import Image
import numpy as np
import tensorflow as tf
from .models import UserTracker
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

# Load your model once globally
import os
import tensorflow as tf

# Absolute path to model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'app', 'models', 'GB_MobileNetV2.h5')

model = tf.keras.models.load_model(MODEL_PATH)
class_names = ['Battery', 'CPU', 'Hard Drive', 'Keyboard', 'Laptop', 'Motherboard', 'Phone', 'RAM']

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

def preprocess_image(image):
    image = image.convert("RGB")
    image = image.resize((224, 224))
    img_array = np.array(image)
    img_array = preprocess_input(img_array)
    return np.expand_dims(img_array, axis=0)

def identify_view(request):
    return render(request, "identify.html")

@csrf_exempt  # make sure to handle CSRF properly in production
def identify_predict(request):
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            image_file = request.FILES['image']
            image = Image.open(image_file)
            processed = preprocess_image(image)
            prediction = model.predict(processed)
            predicted_class_index = np.argmax(prediction)
            predicted_class = class_names[predicted_class_index]

            return JsonResponse({
                'class': predicted_class
            })
        except Exception as e:
            return JsonResponse({'error': str(e)})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def tracker_view(request):
    # Initialize tracker data
    tracker_data = None
    
    # If user is authenticated, get their tracker data
    if request.user.is_authenticated:
        try:
            # Get the user's tracker
            tracker_data = UserTracker.objects.get(user_id=request.user)
        except UserTracker.DoesNotExist:
            # Create a tracker if it doesn't exist
            tracker_data = UserTracker.objects.create(
                user_id=request.user,
                total_devices=0,
                total_co2=0,
                total_kwh=0
            )
    
    # Pass the tracker data to the template
    context = {
        'tracker': tracker_data
    }
    return render(request, "tracker.html", context=context)

def finder_view(request):
    return render(request, "finder.html")

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('identify')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('identify')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('identify')

@login_required
@require_http_methods(["POST"])
def update_tracker(request):
    try:
        # Parse JSON data from request
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'dispose_reuse':
            # Get or create user's tracker
            tracker, created = UserTracker.objects.get_or_create(
                user_id=request.user,
                defaults={
                    'total_devices': 0,
                    'total_co2': 0,
                    'total_kwh': 0
                }
            )
            
            # Increment total_devices by 1
            tracker.total_devices += 1
            tracker.save()
            
            return JsonResponse({
                'success': True,
                'total_devices': tracker.total_devices,
                'message': 'Tracker updated successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Invalid action'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })