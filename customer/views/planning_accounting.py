from django.http import JsonResponse
from customer.models import ProjectDocumentRequirement
import json


def save_document_checklist(request):
    try:
        data = json.loads(request.body)
        
        # Check if a similar document already exists for this project
        existing_document = ProjectDocumentRequirement.objects.filter(
            project_id=data['project_id'],
            name=data['name'],
            type_document=data['type_document']
        ).first()
        
        if existing_document:
            return JsonResponse({
                'status': 'error',
                'message': f'A document with name "{data["name"]}" and type "{data["type_document"]}" already exists for this project.'
            }, status=400)
        
        document = ProjectDocumentRequirement.objects.create(
            project_id=data['project_id'],
            name=data['name'],
            description=data['description'],
            type_document=data['type_document'],
            is_completed=False,
            added_by=request.user)
        document.save()
        documentSerialized = {
            'id': document.id,
            'name': document.name,
            'description': document.description,
            'type_document': document.type_document,
            'is_completed': document.is_completed,
            'file_url': document.file_url,
            'user_name': document.added_by.first_name.split()[0] + ' ' + document.added_by.last_name.split()[0],
            'user_initial': document.added_by.first_name[0] + document.added_by.last_name[0]
        }
        return JsonResponse({
            'status': 'success',
            'message': 'Document saved successfully',
            'data': documentSerialized
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    

def update_document_checklist(request):
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('document_id'):
            return JsonResponse({
                'status': 'error',
                'message': 'Document ID is required'
            }, status=400)
            
        if not data.get('file_url'):
            return JsonResponse({
                'status': 'error',
                'message': 'File URL is required'
            }, status=400)
        
        document = ProjectDocumentRequirement.objects.get(id=data['document_id'])
        
        # Check if document is already completed
        if document.is_completed:
            return JsonResponse({
                'status': 'error',
                'message': 'Document is already completed'
            }, status=400)
        
        document.file_url = data.get('file_url')
        document.is_completed = True
        document.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Document updated successfully'
        })
    except ProjectDocumentRequirement.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Document not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
def delete_document_checklist(request):
    try:
        data = json.loads(request.body)
        document = ProjectDocumentRequirement.objects.get(id=data['document_id'])
        document.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Document deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    