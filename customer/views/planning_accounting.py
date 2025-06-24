from django.http import JsonResponse
from customer.models import ProjectDocumentRequirement
import json


def save_document_checklist(request):
    try:
        data = json.loads(request.body)
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
        print('update_document_checklist');
        print('update_document_checklist');
        print(request.body);
        print('update_document_checklist');
        print('update_document_checklist');
        data = json.loads(request.body)
        print(data);
        document = ProjectDocumentRequirement.objects.get(id=data['document_id'])
        document.file_url = data.get('file_url')
        document.is_completed = True
        print('document', document);
        document.save()
        return JsonResponse({
            'status': 'success',
            'message': 'Document updated successfully'
        })
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
    