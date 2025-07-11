from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ..utils import get_email_full_content
import json

@csrf_exempt
def get_email_full_content_view(request):
    """
    Vista para obtener el contenido completo de un email específico.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            
            if not message_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Message ID is required'
                }, status=400)
            
            # Obtener el contenido completo del email
            email_content = get_email_full_content(message_id)
            
            if email_content is None:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Could not retrieve email content'
                }, status=404)
            
            return JsonResponse({
                'status': 'success',
                'email': email_content
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Only POST method is allowed'
    }, status=405) 