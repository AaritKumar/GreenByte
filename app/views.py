from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from PIL import Image
import base64
import io
from .models import UserTracker, DeviceTracker
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.conf import settings
import anthropic

# Initialize Claude client
claude_client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)

def identify_view(request):
    return render(request, "identify.html")

@csrf_exempt
def identify_predict(request):
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            image_file = request.FILES['image']
            
            # Convert image to base64 for Claude API
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Determine image type
            image_type = image_file.content_type
            if not image_type.startswith('image/'):
                return JsonResponse({'error': 'Invalid image format'})
            
            # Create message for Claude API
            message = claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",  # or claude-3-opus-20240229 for higher accuracy
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": """Identify the electronic device or component in this image and provide comprehensive e-waste guidance. It is crucial that you only identify devices that are electronic. If the item in the image is not an electronic device (e.g., furniture, clothing, non-electronic household items), you must respond with "No Device Detected" for the device name.

Please format your response EXACTLY as follows:

DEVICE: [Name of the electronic device/component]
DEVICE_CO2: [Estimated CO2 emissions for manufacturing this device in kg, as an integer]
DEVICE_KWH: [Estimated kWh of electricity consumed by this device annually, as an integer]

DISPOSAL:
[Provide 3-5 bullet points on how to properly dispose of this device, including:
- E-waste recycling centers
- Manufacturer take-back programs
- Retail drop-off locations
- Special handling requirements (if any)
- Environmental considerations]

REUSE IDEAS:
1. [Creative reuse idea #1]
2. [Creative reuse idea #2]
3. [Creative reuse idea #3]
4. [Creative reuse idea #4]
5. [Creative reuse idea #5]

Focus on practical, safe, and creative ways to repurpose the device or its components. Consider both functional reuses and artistic/decorative purposes. If the device is still functional, prioritize extending its useful life. If it's broken, think about how individual components could be repurposed.

If you cannot clearly identify the device, provide your best assessment and general e-waste guidance, and set CO2 and KWH to 0. If no device is detected, or if the item is not an electronic device, respond with "No Device Detected" for the device name and set all other fields to 0 or empty."""
                            }
                        ]
                    }
                ]
            )
            
            # Extract the response from Claude
            full_response = message.content[0].text.strip()
            
            # Parse the structured response
            device_name = "Unknown Device"
            device_co2 = 0
            device_kwh = 0
            disposal_info = ""
            reuse_ideas = ""
            
            try:
                # Split the response into sections
                sections = full_response.split('\n')
                current_section = None
                disposal_lines = []
                reuse_lines = []
                
                for line in sections:
                    line = line.strip()
                    if line.startswith('DEVICE:'):
                        device_name = line.replace('DEVICE:', '').strip()
                    elif line.startswith('DEVICE_CO2:'):
                        try:
                            device_co2_str = line.replace('DEVICE_CO2:', '').strip().split(' ')[0]
                            device_co2 = int(device_co2_str)
                        except (ValueError, TypeError):
                            device_co2 = 0
                    elif line.startswith('DEVICE_KWH:'):
                        try:
                            device_kwh_str = line.replace('DEVICE_KWH:', '').strip().split(' ')[0]
                            device_kwh = int(device_kwh_str)
                        except (ValueError, TypeError):
                            device_kwh = 0
                    elif line.startswith('DISPOSAL:'):
                        current_section = 'disposal'
                    elif line.startswith('REUSE IDEAS:'):
                        current_section = 'reuse'
                    elif line and current_section == 'disposal':
                        disposal_lines.append(line)
                    elif line and current_section == 'reuse':
                        reuse_lines.append(line)
                
                disposal_info = '\n'.join(disposal_lines)
                reuse_ideas = '\n'.join(reuse_lines)
                
            except Exception as parse_error:
                # If parsing fails, extract device name from the beginning
                lines = full_response.split('\n')
                if lines:
                    first_line = lines[0].strip()
                    if 'DEVICE:' in first_line:
                        device_name = first_line.replace('DEVICE:', '').strip()
                    else:
                        # Fallback: take first few words as device name
                        words = first_line.split()
                        device_name = ' '.join(words[:4]) if len(words) > 4 else first_line
            
            # Clean up device name
            prefixes_to_remove = [
                "This is a ", "This appears to be a ", "I can see a ", 
                "The image shows a ", "This looks like a ", "I identify this as a "
            ]
            
            for prefix in prefixes_to_remove:
                if device_name.lower().startswith(prefix.lower()):
                    device_name = device_name[len(prefix):].strip()
            
            # Remove parenthetical text
            device_name = device_name.split('(')[0].strip()

            # Capitalize first letter
            if device_name:
                device_name = device_name[0].upper() + device_name[1:] if len(device_name) > 1 else device_name.upper()

            if device_name == "No Device Detected":
                return JsonResponse({'class': device_name})

            return JsonResponse({
                'class': device_name,
                'full_response': full_response,
                'disposal_info': disposal_info,
                'reuse_ideas': reuse_ideas,
                'device_co2': device_co2,
                'device_kwh': device_kwh
            })
            
        except anthropic.BadRequestError as e:
            return JsonResponse({'error': f'Claude API error: {str(e)}'})
        except anthropic.RateLimitError as e:
            return JsonResponse({'error': 'Rate limit exceeded. Please try again later.'})
        except anthropic.APIError as e:
            return JsonResponse({'error': f'Claude API error: {str(e)}'})
        except Exception as e:
            return JsonResponse({'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

def tracker_view(request):
    # Initialize tracker data
    tracker_data = None
    devices = None
    
    # If user is authenticated, get their tracker data
    if request.user.is_authenticated:
        try:
            # Get the user's tracker
            tracker_data = UserTracker.objects.get(user_id=request.user)
            devices = DeviceTracker.objects.filter(user=request.user)
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
        'tracker': tracker_data,
        'devices': devices
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
            device_name = data.get('device_name')

            if device_name == "No Device Detected":
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot track "No Device Detected"'
                })

            device_co2 = data.get('device_co2', 0)
            device_kwh = data.get('device_kwh', 0)

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
            tracker.total_co2 += device_co2
            tracker.total_kwh += device_kwh
            tracker.save()

            # Create a new DeviceTracker entry
            DeviceTracker.objects.create(
                user=request.user,
                device_name=device_name,
                device_co2=device_co2,
                device_kwh=device_kwh
            )
            
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