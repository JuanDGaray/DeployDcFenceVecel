from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.http import JsonResponse
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
from googleapiclient.http import MediaIoBaseUpload
import json
from .models import (Project, Notification)
from django.shortcuts import get_object_or_404
import os
import requests
import re
from django.contrib.auth.models import User
import time
import base64
from email.mime.text import MIMEText
import html
import email
from email import policy


drive_id = '0AF4IswhouZv_Uk9PVA'

class GoogleService:
    _service = None
    _creds = None
    _creds_gmail = None
    _gmail_service = None

    @staticmethod
    def get_service():
        if GoogleService._service is None:
            credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS', '{}'))
            credentials_gmail = json.loads(os.getenv('GMAIL_CREDENTIALS', '{}'))
            if 'private_key' in credentials_info:
                credentials_info['private_key'] = credentials_info['private_key'].replace("\\n", "\n")
                
            if 'private_key' in credentials_gmail:
                credentials_gmail['private_key'] = credentials_gmail['private_key'].replace("\\n", "\n")    
            
            creds = Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/drive",
                        ]
            )
            
            creds_gmail = Credentials.from_service_account_info(
                credentials_gmail,
                scopes=["https://mail.google.com/"],
                subject='dcfenceapp@dcfence.org'
            )
            
                
            # Refrescar las credenciales si es necesario
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            if creds_gmail.expired and creds_gmail.refresh_token:
                creds_gmail.refresh(Request())
            
            GoogleService._creds = creds
            GoogleService._service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            GoogleService._gmail_service = build('gmail', 'v1', credentials=creds_gmail)
        return {'drive': GoogleService._service,
                'gmail': GoogleService._gmail_service}
        
    @staticmethod
    def get_creds():
        if GoogleService._creds is None:
            GoogleService.get_service()
        return GoogleService._creds

mime_to_extension = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/svg+xml": "svg",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
    "image/x-icon": "ico",
    "image/vnd.microsoft.icon": "ico",
    "image/heif": "heif",
    "image/heic": "heic",
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
}

def fetch_children(request, folder_id):
    try:
        parent_folder_id = '0AF4IswhouZv_Uk9PVA'
        service = GoogleService.get_service()['drive']
        print(folder_id)
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            corpora='drive', 
            driveId=parent_folder_id, 
            q=query,
            fields="files(id, name, mimeType, size)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()
        files = results.get('files', [])
        structure = []
        for file in files:
            if file['mimeType'] in mime_to_extension:
                extension = 'filetype-'+mime_to_extension[file['mimeType']]
            else:
                extension = "file-earmark"   
            formatName = file['mimeType'].split('/')[-1]
            structure.append({
                "id": file['id'],
                "name": file['name'],
                "type": "file",
                "url": f"https://drive.google.com/file/d/{file['id']}/preview",
                "size": file['size'],
                "mimeType": extension,
                "formatName": formatName
            })
        return JsonResponse({"message": "Estructura obtenida con éxito", "structure": structure})
    except HttpError as error:
        return JsonResponse({"message": "Error al obtener la estructura", "error": str(error)}, status=500)


@csrf_exempt
def get_folders_in_drive(request):
    try:
        if request.method == 'POST':
            folder_id= request.POST.get('folder_id')

            
            if not folder_id:
                return JsonResponse({'error': 'El nombre del proyecto es necesario'}, status=400)

            service = GoogleService.get_service()['drive']  # Asegúrate de implementar esta
            parent_folder_id = '0AF4IswhouZv_Uk9PVA'

            query = f"'{folder_id}' in parents and trashed = false"

            results = service.files().list(
                corpora="drive",
                driveId=parent_folder_id,
                q=query,
                fields="files(id, name, mimeType)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            
            project_folders = results.get('files', [])
            if not project_folders:
                return JsonResponse({"message": "No se encontró ninguna carpeta para el proyecto", "structure": []})

            structure = []
            for folder in project_folders:
                structure.append({
                    "id": folder['id'],
                    "name": folder['name'],
                    "type": "folder",})
            return JsonResponse({"message": "Estructura obtenida con éxito", "structure": sorted(structure, key=lambda x: x['name'])})
    except HttpError as error:
        return JsonResponse({"message": "Error al obtener la estructura", "error": str(error)}, status=500)

@csrf_exempt
def delete_file_to_drive(request):
    '''The function `delete_file_to_drive` deletes a file by moving it to the trash in Google Drive based
    on the provided file ID.
    
    Parameters
    ----------
    request
        The `request` parameter in the `delete_file_to_drive` function is typically an HTTP request object
    that contains information about the incoming request, such as the request method (e.g., GET, POST),
    headers, body, and other relevant data. In this context, the function is expecting a POST
    
    Returns
    -------
        The function `delete_file_to_drive` returns a JSON response with a message indicating the outcome
    of the file deletion operation. The possible return messages are:
    1. If the file is successfully moved to the trash: {'message': 'File moved to trash successfully'}
    2. If there is no file ID provided in the request: {'message': 'No file ID provided'}
    3. If there is an
    
    '''
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_id = data.get('file_id')
            if not file_id:
                return JsonResponse({'message': 'No file ID provided'}, status=400)

            service = GoogleService.get_service()['drive']
            file_metadata = {'trashed': True}
            response = service.files().update(fileId=file_id, body=file_metadata, supportsAllDrives=True).execute()

            if response:
                return JsonResponse({'message': 'File moved to trash successfully'})
            else:
                return JsonResponse({'message': 'Failed to move the file to trash'}, status=500)
        except json.JSONDecodeError:
            return JsonResponse({'message': 'Invalid JSON format'}, status=400)
        except HttpError as error:
            return JsonResponse({'message': f"Error al mover el archivo a la papelera: {str(error)}"}, status=500)

    return JsonResponse({'message': 'Invalid request'}, status=400)

def create_folder_in_drive(request):
    '''The function `create_folder_in_drive` creates a new folder in Google Drive based on the provided
    request data.
    
    Parameters
    ----------
    request
        The function `create_folder_in_drive` is designed to create a new folder in Google Drive using the
    Google Drive API. It expects a POST request containing JSON data with the keys 'folder_name' and
    'folder_root' (optional) specifying the name of the new folder and the parent folder ID where
    
    Returns
    -------
        If the request method is 'POST' and the folder creation is successful, a JSON response will be
    returned with the message 'Folder created successfully', along with the folder ID and name. If the
    folder name is missing or if the method is not allowed, appropriate error messages will be returned.
    
    '''
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)  # Convertir JSON a diccionario

        folder_name = data.get('folder_name', 'New Folder')  # Valor por defecto
        parent_folder_id = data.get('folder_root')
        if not folder_name:
            return JsonResponse({'message': 'Folder name is required'}, status=400)

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]
        
            service = GoogleService.get_service()['drive']
            folder = service.files().create(
                body=file_metadata,
                fields='id, name',
                supportsAllDrives=True 
            ).execute()

            return JsonResponse({
                'message': 'Folder created successfully',
                'folder_id': folder['id'],
                'folder_name': folder['name']
            })
    return JsonResponse({'message': 'Method not allowed'}, status=405)

def rename_folder_in_drive(request):
    '''The function `rename_folder_in_drive` renames a folder in Google Drive based on the provided folder
    ID and new folder name.
    
    Parameters
    ----------
    request
        The `request` parameter in the `rename_folder_in_drive` function is typically an HTTP request
    object that contains information about the incoming request, such as the method (POST, GET, etc.)
    and any data sent along with the request (e.g., form data). In this context, it is
    
    Returns
    -------
        The function `rename_folder_in_drive` returns a JSON response with a success message if the folder
    renaming operation is successful. It includes the updated folder ID and name in the response. If
    there is an error during the renaming process, it returns a JSON response with an error message. If
    the HTTP method is not POST, it returns a JSON response indicating that the method is not allowed.
    
    '''
    if request.method == 'POST':

        folder_id = request.POST.get('folder_id')
        new_folder_name = request.POST.get('new_folder_name') 

        if not folder_id or not new_folder_name:
            return JsonResponse({'message': 'Folder ID and new folder name are required'}, status=400)
        service = GoogleService.get_service()

        try:
            file_metadata = {'name': new_folder_name}
            updated_folder = service.files().update(
                fileId=folder_id,
                body=file_metadata,
                fields='id, name',
                supportsAllDrives=True
            ).execute()


            return JsonResponse({
                'message': 'Folder renamed successfully',
                'folder_id': updated_folder['id'],
                'folder_name': updated_folder['name']
            })
        except HttpError as error:
            return JsonResponse({'message': 'Error renaming the folder', 'error': str(error)}, status=500)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

def create_folders_by_projects(folder_name):
    '''The function `create_folders_by_projects` creates a main folder and subfolders within it in Google
    Drive based on a given folder name.
    
    Parameters
    ----------
    folder_name
        The `folder_name` parameter in the `create_folders_by_projects` function is the name of the main
    folder that will be created in Google Drive. This function creates a main folder with the specified
    name and then creates several subfolders within it, each with a specific name as listed in the `sub
    
    Returns
    -------
        The function `create_folders_by_projects` returns a dictionary with information about the created
    folders. If the operation is successful, it returns a dictionary with keys 'status', 'folder_id',
    and 'folder_name' containing the status of the operation, the ID of the main folder created, and the
    name of the main folder created, respectively. If an error occurs during the process, it returns a
    dictionary
    
    '''
    try:
        file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
        }
        file_metadata['parents'] = [drive_id]

        service = GoogleService.get_service()['drive']
        folder = service.files().create(
            body=file_metadata,
            fields='id, name',
            supportsAllDrives=True 
        ).execute()

        subfolders = [
            'SOV', 'Invoices', 'ChangeOrder',
            'Permit', 'Documents', 'Plans/Drawings', 
            'Proposal', 'Evidence', 'Material', 'COI Insurance', 'NTC/PO', 'Contract'
        ]
        created_subfolders = []

        for subfolder_name in subfolders:
            subfolder_metadata = {
                'name': subfolder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [folder['id']] 
            }

            subfolder = service.files().create(
                body=subfolder_metadata,
                fields='id, name',
                supportsAllDrives=True
            ).execute()

            created_subfolders.append({
                'subfolder_id': subfolder['id'],
                'subfolder_name': subfolder['name']
            })

        return {
            'status': 'success',
            'folder_id': folder['id'],
            'folder_name': folder['name']
        }

    except Exception as e:
        return {'status': 'error', 'message': str(e)}
    
def delete_folders_by_projects(folder_name, folder_root_value):
    '''The function `delete_folders_by_projects` deletes a folder specified by its ID using the Google
    Drive API.
    
    Parameters
    ----------
    folder_name
        The `folder_name` parameter is the name of the folder that you want to delete.
    folder_root_value
        The `folder_root_value` parameter in the `delete_folders_by_projects` function is the unique
    identifier of the folder in Google Drive that you want to delete. It is used to specify the folder
    that needs to be trashed (deleted).
    
    Returns
    -------
        The function `delete_folders_by_projects` returns a dictionary with a 'status' key indicating
    whether the operation was successful or resulted in an error. If successful, the 'status' key will
    have a value of 'success'. If an error occurs during the execution of the function, the 'status' key
    will have a value of 'error', and the 'message' key will contain a string representation
    
    '''
    try:
        service = GoogleService.get_service()['drive']
        file_metadata = {'trashed': True}
        service.files().update(fileId=folder_root_value, body=file_metadata, supportsAllDrives=True).execute()
        return {
            'status': 'success',
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def list_all_folders(service, drive_id):
    try:
        # Lista para almacenar todas las carpetas
        all_folders = []
        page_token = None
        
        # Consulta para obtener solo carpetas
        query = "mimeType = 'application/vnd.google-apps.folder'"
        
        while True:
            # Llamada a la API para obtener las carpetas
            response = service.files().list(
                q=query, 
                spaces='drive', 
                fields='nextPageToken, files(id, name)', 
                pageToken=page_token,
                corpora='drive',  # Establece corpora como 'drive' para especificar el contexto del drive
                driveId=drive_id,  # Asegúrate de pasar el ID del drive correcto
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            
            # Agregar las carpetas a la lista
            for file in response.get('files', []):
                all_folders.append({'id': file.get('id'), 'name': file.get('name')})
            
            # Imprimir las carpetas encontradas
            for folder in all_folders:
                print(f"Folder Name: {folder['name']}, ID: {folder['id']}")
            
            # Verificar si hay una página siguiente
            page_token = response.get('nextPageToken', None)
            if not page_token:
                break  # No hay más carpetas, terminamos el ciclo

        return all_folders
    
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

@csrf_exempt
def upload_file_to_drive(request):
    if request.method == 'POST':
        try:
            service = GoogleService.get_service()['drive']
            file_name = request.POST.get('file_name')
            mimeType = request.POST.get('mimeType')
            folder_id = str(request.POST.get('folder_id'))
            origin = request.META.get('HTTP_ORIGIN')
            is_evidence = request.POST.get('is_evidence')
            
            # Validate and set default MIME type if not provided or invalid
            if not mimeType or mimeType == 'file' or mimeType == '':
                mimeType = 'application/octet-stream'
            
            if is_evidence:
                folder_name = 'Evidence'
                folder_id = search_folder_in_drive(folder_id, folder_name)
            
            file_metadata = {
                'mimeType': mimeType,
                'name': file_name,
                'parents': [folder_id],
            }
            headers = {'Content-Type': 'application/json; charset=UTF-8',
                       'X-Upload-Content-Type': mimeType,
                       'Authorization': f'Bearer {service._http.credentials.token}',
                       'Origin': origin}
            
            params = {
                'corpora': 'drive',
                'driveId': drive_id,
                'includeItemsFromAllDrives': 'true',
                'supportsAllDrives': 'true', 
            }

            try:
                response = requests.post(
                    'https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable',
                    headers=headers,
                    json=file_metadata,
                    params=params,
                )
                
                if response.status_code != 200:
                    print(f"Failed to initiate resumable upload: {response.text}")
                    return JsonResponse({'message': 'Failed to initiate resumable upload'}, status=500)
                print(response.headers)
                upload_url = response.headers['Location']
                return JsonResponse({'uploadUrl': upload_url}, status=200)

            except HttpError as error:
                print(f"Failed to upload {file_name}: {error}")
        except Exception as e:
             print(f"Error occurred: {str(e)}")
             return JsonResponse({'message': f'Error occurred: {str(e)}'}, status=500)
    
    return JsonResponse({'message': 'Method not allowed'}, status=405)



def search_folder_in_drive(folder_id, folder_name, drive_id=None):
    try:
        service = GoogleService.get_service()['drive']
        query = f"'{folder_id}' in parents and name='{folder_name}' and trashed=false"

        kwargs = {
            'q': query,
            'fields': 'files(id, name)',
            'includeItemsFromAllDrives': True,
            'supportsAllDrives': True
        }

        # Si se especifica un drive_id (es un Shared Drive)
        if drive_id:
            kwargs['corpora'] = 'drive'
            kwargs['driveId'] = drive_id
        else:
            kwargs['corpora'] = 'user'

        results = service.files().list(**kwargs).execute()

        folder_evidence = results.get('files', [])
        return folder_evidence[0]['id'] if folder_evidence else None
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return None


def search_file_in_drive(folder_id, file_name):
    '''The function `search_file_in_drive` searches for a file in a specific folder in Google Drive,
    creates a copy if the file is not found, and returns the file or list of files found.
    
    Parameters
    ----------
    folder_id
        The `folder_id` parameter in the `search_file_in_drive` function is used to specify the ID of the
    folder in Google Drive where you want to search for a file. This ID uniquely identifies the folder
    within Google Drive and helps the function to locate the correct folder for file operations.
    file_name
        The `file_name` parameter in the `search_file_in_drive` function is used to specify the name of the
    file that you want to search for within a specific folder in Google Drive. The function will search
    for this file within the folder specified by the `folder_id` parameter. If the file
    
    Returns
    -------
        The function `search_file_in_drive` is returning either a list of files in the specified folder, a
    newly copied file if the specified file is not found in the folder, or the existing file if it is
    found in the folder.
    
    '''
    try:
        print(folder_id)
        service = GoogleService.get_service()['drive']
        query = f"'{folder_id}' in parents and name='Invoices' and trashed=false"
        results = service.files().list(
            corpora='drive', 
            driveId=drive_id, 
            q=query,
            fields="files(id, name, mimeType)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()

        # Obtener lista de archivos
        files = results.get('files', [])
        for file in files:
            if file['name'] == 'Invoices':
                query_in_proposal = f"'{file['id']}' in parents and name='{file_name}' and trashed=false"
                proposal_results = service.files().list(
                    q=query_in_proposal,
                    corpora='drive', 
                    driveId=drive_id,
                    fields='files(id, name)',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                ).execute()
                proposal_files = proposal_results.get('files', [])
                if not proposal_files:
                    print("No se encontró el archivo 'File Name'. Creando una copia.")
                    if file_name == 'AIA TEMPLATE 5% GC':
                        source_file_id = "1ecGnmQET5VlTu85feqYN8HYnKkRLWGAG"
                    if file_name == 'AIA TEMPLATE 10% GC':
                        source_file_id = "1LZQ056f1pCvMwn3qpacmy_yGYOamlgOd"
                    new_file_metadata = {
                        'name': file_name,
                        'parents': [file['id']]
                    }
                    copied_file = service.files().copy(
                        fileId=source_file_id,
                        body=new_file_metadata,
                        supportsAllDrives=True
                    ).execute()

                    print(f"Archivo copiado exitosamente: {copied_file['name']} (ID: {copied_file['id']})")
                    return copied_file
                else:
                    print("El archivo 'File Name' ya existe en la carpeta 'Proposal'.")
                    return proposal_files
                
        return files

    except Exception as e:
        print(f"Error al listar archivos en la carpeta: {e}")
        return []
    
    '''The function `search_aia5_in_drive` searches for a specific file in a Google Drive folder, creates a
    copy if the file is not found, and returns the file information.
    
    Parameters
    ----------
    folder_id
        The `folder_id` parameter in the `search_aia5_in_drive` function is used to specify the ID of the
    folder in Google Drive where the search operation will be performed. This ID uniquely identifies the
    folder within Google Drive.
    file_name
        It looks like you were about to provide some information about the `file_name` parameter, but the
    information is missing. Could you please provide more details or let me know if you need help with
    something specific related to the `file_name` parameter?
    
    Returns
    -------
        The function `search_aia5_in_drive` is returning either the copied file if it doesn't exist in the
    folder, the existing file if it does exist, or the list of files in the folder if the 'Invoices'
    folder itself doesn't exist.
    
    '''
    try:
        service = GoogleService.get_service()['drive']
        query = f"'{folder_id}' in parents and name='Invoices' and trashed=false"
        results = service.files().list(
            corpora='drive', 
            driveId=drive_id, 
            q=query,
            fields="files(id, name, mimeType)",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True
        ).execute()

        # Obtener lista de archivos
        files = results.get('files', [])
        for file in files:
            if file['name'] == 'Invoices':
                query_in_proposal = f"'{file['id']}' in parents and name='{file_name}' and trashed=false"
                proposal_results = service.files().list(
                    q=query_in_proposal,
                    corpora='drive', 
                    driveId=drive_id,
                    fields='files(id, name)',
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                ).execute()
                print(proposal_results)
                proposal_files = proposal_results.get('files', [])
                if not proposal_files:
                    print("No se encontró el archivo 'File Name'. Creando una copia.")
                    source_file_id = "1ecGnmQET5VlTu85feqYN8HYnKkRLWGAG"  
                    new_file_metadata = {
                        'name': file_name,
                        'parents': [file['id']]
                    }
                    copied_file = service.files().copy(
                        fileId=source_file_id,
                        body=new_file_metadata,
                        supportsAllDrives=True
                    ).execute()

                    print(f"Archivo copiado exitosamente: {copied_file['name']} (ID: {copied_file['id']})")
                    return copied_file
                else:
                    print("El archivo 'File Name' ya existe en la carpeta 'Proposal'.")
                    return proposal_files
                
        return files

    except Exception as e:
        return []

def new_aia5_xlxs_template(request,project_id):
    project = get_object_or_404(Project, pk=project_id)
    folderID = project.folder_id
    result = search_file_in_drive(folderID, 'AIA TEMPLATE 5% GC')
    return JsonResponse({'data': result})  

def new_aia10_xlxs_template(request,project_id):
    project = get_object_or_404(Project, pk=project_id)
    folderID = project.folder_id
    result = search_file_in_drive(folderID, 'AIA TEMPLATE 10% GC')
    return JsonResponse({'data': result})  



from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import base64

def send_email(subject, html_body, recipient_email, project_id=None, proposal_id=None):
    """
    Envía un correo electrónico con contenido HTML utilizando la API de Gmail.

    Args:
        subject (str): Asunto del correo.
        html_body (str): Contenido HTML del mensaje.
        recipient_email (str): Dirección de correo del destinatario.
        project_id (int, optional): ID del proyecto para seguimiento.
        proposal_id (int, optional): ID de la propuesta para seguimiento.

    Returns:
        dict: Resultado del envío con 'status' y detalles adicionales.
    """
    try:
        service = GoogleService.get_service()['gmail']

        # Crear el mensaje con HTML
        message = MIMEText(html_body, 'html')  # Ahora el mensaje es HTML
        message['to'] = recipient_email
        message['from'] = "dcfenceapp@dcfence.org"  # Usar el correo correcto de DC Fence
        message['subject'] = subject
        # Agregar headers personalizados para seguimiento
        if project_id:
            message['X-Project-Id'] = f'P{project_id}'
        if proposal_id:
            message['X-Proposal-Id'] = f'PR{proposal_id}'

        # Codificar el mensaje en base64url
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Enviar el mensaje
        send_message = (
            service.users()
            .messages()
            .send(userId='me', body={'raw': raw_message})
            .execute()
        )

        return {'status': 'success', 'messageId': send_message['id']}
    
    except HttpError as error:
        return {'status': 'error', 'message': str(error)}

    except Exception as e:
        return {'status': 'error', 'message': f"Unexpected error: {e}"}


def send_reply_email(subject, html_body, recipient_email, original_message_id=None, project_id=None, proposal_id=None):
    """
    Envía una respuesta a un email utilizando la API de Gmail.
    Configura los headers apropiados para que se reconozca como una respuesta.

    Args:
        subject (str): Asunto del correo (debe incluir "Re:").
        html_body (str): Contenido HTML del mensaje.
        recipient_email (str): Dirección de correo del destinatario.
        original_message_id (str, optional): ID del mensaje original al que se responde.
        project_id (int, optional): ID del proyecto para seguimiento.
        proposal_id (int, optional): ID de la propuesta para seguimiento.

    Returns:
        dict: Resultado del envío con 'status' y detalles adicionales.
    """
    try:
        service = GoogleService.get_service()['gmail']

        # Agregar footer profesional con logo y slogan
        professional_footer = """
        <div style="margin-top: 30px; padding-top: 20px; border-top: 2px solid #e0e0e0; text-align: center; font-family: Arial, sans-serif;">
            <div style="color: #666; font-size: 14px; font-style: italic; margin-bottom: 10px;">
                <strong>2500 W 3 Ct Hialeah FL 33010</strong>
                <br>
                <strong>(O) 786-747-4766</strong>
                <br>
                <strong>(F)  786-747-4766</strong>
                <br>
                "Because everyone needs Boundaries”"
            </div>
            <div style="margin-bottom: 15px;">
                <img src="https://office.dcfence.org/static/img/LogoCompleteLarge.png" alt="DC FENCE" style="max-width: 200px; height: auto;">
            </div>
            <div style="color: #999; font-size: 12px;">
                <strong>Lic: 20BS00539/21-F22501-R</strong>
                <br>
                <strong>SBE-CON/SBE-G&S/LDB CAGE:8ZKA7 Duns:117970612</strong>
            </div>
            </div>
        </div>
        """
        
        # Combinar el contenido del email con el footer
        complete_html_body = html_body + professional_footer

        # Crear el mensaje con HTML
        message = MIMEText(complete_html_body, 'html')
        message['to'] = recipient_email
        message['from'] = "dcfenceapp@dcfence.org"
        message['subject'] = subject
        
        # Agregar headers para que se reconozca como respuesta
        # Los headers In-Reply-To y References deben contener el Message-ID del email original
        if original_message_id:
            # Obtener el Message-ID del email original
            try:
                original_msg = service.users().messages().get(
                    userId='me',
                    id=original_message_id,
                    format='metadata',
                    metadataHeaders=['Message-ID']
                ).execute()
                
                # Extraer el Message-ID del email original
                headers = original_msg.get('payload', {}).get('headers', [])
                original_message_id_header = None
                for header in headers:
                    if header.get('name', '').lower() == 'message-id':
                        original_message_id_header = header.get('value', '')
                        break
                
                if original_message_id_header:
                    message['In-Reply-To'] = original_message_id_header
                    message['References'] = original_message_id_header
                    
            except Exception as e:
                pass
        
        # Agregar headers personalizados para seguimiento
        if project_id:
            message['X-Project-Id'] = f'P{project_id}'
        if proposal_id:
            message['X-Proposal-Id'] = f'PR{proposal_id}'

        # Codificar el mensaje en base64url
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Enviar el mensaje
        send_message = (
            service.users()
            .messages()
            .send(userId='me', body={'raw': raw_message})
            .execute()
        )

        return {'status': 'success', 'messageId': send_message['id']}
    
    except HttpError as error:
        return {'status': 'error', 'message': str(error)}

    except Exception as e:
        return {'status': 'error', 'message': f"Unexpected error: {e}"}

def extract_mentions(text):
    """
    Extrae las menciones (@username) del texto y retorna una lista de usernames
    """
    mention_pattern = r'@(\w+)'
    mentions = re.findall(mention_pattern, text)
    return mentions

def get_users_from_mentions(mentions):
    """
    Obtiene los usuarios basado en las menciones
    """
    users = []
    for username in mentions:
        try:
            user = User.objects.get(username=username)
            users.append(user)
        except User.DoesNotExist:
            continue
    return users

def create_mention_notifications(comment, mentioned_users, sender):
    """
    Crea notificaciones para usuarios mencionados
    """
    for user in mentioned_users:
        if user != sender:  # No notificar al propio usuario
            Notification.objects.create(
                recipient=user,
                sender=sender,
                notification_type='mention',
                project=comment.project,
                comment=comment,
                message=f'{sender.get_full_name()} mentioned you in a comment on project "{comment.project.project_name}"'
            )

def create_reply_notification(comment, sender):
    """
    Crea notificación para el autor del comentario padre cuando alguien responde
    """
    if comment.parent_comment and comment.parent_comment.user != sender:
        Notification.objects.create(
            recipient=comment.parent_comment.user,
            sender=sender,
            notification_type='reply',
            project=comment.project,
            comment=comment,
            message=f'{sender.get_full_name()} replied to your comment on project "{comment.project.project_name}"'
        )

def create_manager_assignment_notification(project, manager, manager_type, assigned_by):
    """
    Crea notificación cuando se asigna un manager (accounting o production) a un proyecto
    
    Args:
        project: Instancia del proyecto
        manager: Usuario asignado como manager
        manager_type: Tipo de manager ('accounting' o 'production')
        assigned_by: Usuario que realizó la asignación
    """
    manager_type_display = 'Accounting Manager' if manager_type == 'accounting' else 'Project Manager'
    
    Notification.objects.create(
        recipient=manager,
        sender=assigned_by,
        notification_type='manager_assignment',
        project=project,
        message=f'You have been assigned as {manager_type_display} for project "{project.project_name}" by {assigned_by.get_full_name()}'
    )

def format_comment_with_mentions(text):
    """
    Formatea el texto del comentario para mostrar las menciones como enlaces
    """
    mention_pattern = r'@(\w+)'
    
    def replace_mention(match):
        username = match.group(1)
        try:
            user = User.objects.get(username=username)
            return f'<span class="mention" data-username="{username}">@{username}</span>'
        except User.DoesNotExist:
            return match.group(0)
    
    return re.sub(mention_pattern, replace_mention, text)

def get_html_payload(payload):
    """
    Extrae el contenido HTML o texto plano del payload de Gmail API.
    Maneja diferentes tipos de contenido incluyendo multipart y emails de respuesta.
    """
    if not payload:
        return ""
    
    # Si es text/html directo
    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4)).decode("utf-8", errors="replace")
    
    # Si es text/plain, convertir a HTML
    elif payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            text = base64.urlsafe_b64decode(data + '=' * (-len(data) % 4)).decode("utf-8", errors="replace")
            # Convertir saltos de línea a <br> y envolver en HTML básico
            return f"<div style='font-family: Arial, sans-serif; line-height: 1.6;'>{text.replace(chr(10), '<br>').replace(chr(13), '')}</div>"
    
    # Si es multipart (más común en emails de respuesta)
    elif payload.get("mimeType", "").startswith("multipart/"):
        parts = payload.get("parts", [])
        
        # Buscar primero contenido HTML
        for part in parts:
            if part.get("mimeType") == "text/html":
                html = get_html_payload(part)
                if html:
                    return html
        
        # Si no hay HTML, buscar texto plano
        for part in parts:
            if part.get("mimeType") == "text/plain":
                html = get_html_payload(part)
                if html:
                    return html
        
        # Si no hay partes directas, buscar en subpartes
        for part in parts:
            if part.get("mimeType", "").startswith("multipart/"):
                html = get_html_payload(part)
                if html:
                    return html
    
    # Si no se encontró contenido, devolver un mensaje de error
    return "<div style='color: #666; font-style: italic;'>No se pudo cargar el contenido del email</div>"

def extract_headers(message_payload):
    """
    Recibe el objeto 'msg' completo o directamente msg['payload'].
    Devuelve un dict con subject, date, from, to (minúsculas).
    """
    headers_list = message_payload['headers']  # lista de headers
    wanted = {'subject', 'date', 'from', 'to'}
    result = {}

    for h in headers_list:
        name = h.get('name', '').lower()
        if name in wanted:
            result[name] = h.get('value', '')

            # Salir temprano si ya tenemos los 4
            if len(result) == len(wanted):
                break

    # Si algún header no está, poner cadena vacía
    for key in wanted:
        result.setdefault(key, '')

    return result


# --- NUEVA FUNCION AUXILIAR ---
def extract_attachments_metadata(payload):
    """
    Extrae metadatos de los archivos adjuntos del payload de Gmail API.
    Devuelve una lista de dicts con filename, mime_type, size, attachment_id.
    """
    attachments = []
    def process_parts(parts):
        for part in parts:
            if part.get('filename') and part.get('body', {}).get('attachmentId'):
                attachments.append({
                    'filename': part['filename'],
                    'mime_type': part.get('mimeType', 'application/octet-stream'),
                    'size': part.get('body', {}).get('size', 0),
                    'attachment_id': part['body']['attachmentId']
                })
            if part.get('parts'):
                process_parts(part['parts'])
    if payload.get('parts'):
        process_parts(payload['parts'])
    elif payload.get('body', {}).get('attachmentId'):
        attachments.append({
            'filename': payload.get('filename', 'attachment'),
            'mime_type': payload.get('mimeType', 'application/octet-stream'),
            'size': payload.get('body', {}).get('size', 0),
            'attachment_id': payload['body']['attachmentId']
        })
    return attachments

# --- MODIFICAR get_emails_sent_to_client ---
def get_emails_sent_to_client(client_email, project_id=None):
    """
    Extract all emails sent to a specific client using the Gmail API.
    If project_id is provided, filters by X-Project-Id header.
    
    Args:
        client_email (str): Email address of the client to search.
        project_id (int, optional): Project ID to filter emails by X-Project-Id header.
        
    Returns:
        dict: Result with 'status' and list of found emails or error message.
    """
    try:
        # Get the Gmail service
        service = GoogleService.get_service()['gmail']
        
        # Build queries to search for emails sent to the client AND emails from the client
        query_sent = f'to:{client_email}'
        query_received = f'from:{client_email}'
        
        # NOTA: Gmail API no permite buscar directamente por headers personalizados
        # Solo campos estándar como subject, from, to, etc.
        # Por eso usamos batch request para filtrar después
        if project_id:
            query_sent += f' subject:"P{project_id}"'
            query_received += f' subject:"P{project_id}"'
        
                # Perform the search for messages sent TO the client
        try:
            results_sent = service.users().messages().list(
                userId='me',
                q=query_sent,
                maxResults=100,
                fields="messages(id,snippet,internalDate,payload/headers)"
            ).execute()
        except Exception as e:
            print(f"Error al buscar emails enviados: {str(e)}")
            results_sent = {'messages': []}
        
        # Perform the search for messages received FROM the client
        try:
            results_received = service.users().messages().list(
                userId='me',        
                q=query_received,
                maxResults=100,
                fields="messages(id,snippet,internalDate,payload/headers)"
            ).execute()
        except Exception as e:
            print(f"Error al buscar emails recibidos: {str(e)}")
            results_received = {'messages': []}
        
        # Combine both results
        messages_sent = results_sent.get('messages', [])
        messages_received = results_received.get('messages', [])
        
        # Combine and deduplicate messages
        all_messages = messages_sent + messages_received
        # Remove duplicates based on message ID
        seen_ids = set()
        unique_messages = []
        for msg in all_messages:
            if msg['id'] not in seen_ids:
                seen_ids.add(msg['id'])
                unique_messages.append(msg)
        
        messages = unique_messages
        
        # Sort messages by date in descending order (most recent first)
        # We'll sort after getting the full message details since we need the date
        
        if not messages:
            if project_id:
                return {
                    'status': 'success',
                    'message': f'No se encontraron correos relacionados con {client_email} y P{project_id}',
                    'emails': []
                }
            else:
                return {
                    'status': 'success',
                    'message': f'No se encontraron correos relacionados con {client_email}',
                    'emails': []
                }
        
        # Procesar todos los emails encontrados
        emails_details = []
        
        # Procesar todos los emails encontrados
        if messages:

            for message in messages:
                try:
                    # Obtener el email completo con formato raw
                    try:
                        msg = service.users().messages().get(
                            userId='me',
                            id=message['id'],
                            format='full'
                        ).execute()
                    except Exception as e:
                        print(f"Error al obtener mensaje {message['id']}: {str(e)}")
                        continue

                    
                    
                    headers = extract_headers(msg['payload'])  # 👈 usa la función nueva

                    subject = headers['subject']
                    date    = headers['date']
                    from_header   = headers['from']  
                    to_header      = headers['to']
                    html_payload = get_html_payload(msg['payload'])
                    
                    # Extract project_id and proposal_id from subject and headers (flexible)
                    project_id_from_subject = None
                    proposal_id_from_subject = None
                    import re
                    # First try to get from custom headers
                    x_project_id = headers.get('x-project-id')
                    x_proposal_id = headers.get('x-proposal-id')
                    x_tracking_id = headers.get('x-tracking-id')

                    
                    if x_project_id:
                        project_match = re.search(r'P(\d+)', x_project_id)
                        if project_match:
                            project_id_from_subject = int(project_match.group(1))
                    if x_proposal_id:
                        proposal_match = re.search(r'PR(\d+)', x_proposal_id)
                        if proposal_match:
                            proposal_id_from_subject = int(proposal_match.group(1))
                    
                    # If not found in headers, try subject
                    if not project_id_from_subject:
                        pattern = r'P(\d+)(?:PR|Pr)?(\d+)?'
                        match = re.search(pattern, subject)
                        if match:
                            project_id_from_subject = int(match.group(1))
                            
                            if match.group(2):
                                proposal_id_from_subject = int(match.group(2))
                    

                    
                    # Determine if this is an email we sent or received
                    is_sent_by_us = from_header.lower().find('dcfenceapp@dcfence.org') != -1
                    
                    # Extract email body from raw format (simplified)
                    email_body = msg.get('snippet', '')
                    
                    # Determinar si el email ha sido leído usando las labels de Gmail
                    # Gmail usa la label 'UNREAD' para emails no leídos
                    # Si el email tiene la label 'UNREAD', no ha sido leído
                    labels = msg.get('labelIds', [])
                    is_unread = 'UNREAD' in labels
                    
                    # Los emails enviados siempre se consideran leídos
                    # Los emails recibidos se marcan como no leídos si tienen la label 'UNREAD'
                    is_read = is_sent_by_us or not is_unread
                    
                    # --- NUEVO: extraer adjuntos ---
                    attachments = extract_attachments_metadata(msg['payload'])
                

                    email_info = {
                        'id': message['id'],
                        'subject': subject,
                        'date': date,
                        'from': from_header,
                        'to': to_header,
                        'snippet': msg.get('snippet', ''),
                        'body': html_payload,
                        'project_id': project_id_from_subject,
                        'proposal_id': proposal_id_from_subject,
                        'tracking_id': x_tracking_id,
                        'direction': 'sent' if is_sent_by_us else 'received',
                        'read': is_read,
                        'attachments': attachments  # <--- AQUI
                    }
                    
                    emails_details.append(email_info)
                    
                except Exception as e:
                    print(f"Error al procesar mensaje {message['id']}: {str(e)}")
                    continue
            
            # Sort emails by date in descending order (most recent first)
            emails_details.sort(key=lambda x: x['date'], reverse=True)
            


        if project_id:
            return {
                'status': 'success',
                'message': f'Se encontraron {len(emails_details)} correos relacionados con {client_email} y P{project_id}',
                'emails': emails_details
            }
        else:
            return {
                'status': 'success',
                'message': f'Se encontraron {len(emails_details)} correos relacionados con {client_email}',
                'emails': emails_details
            }
        
    except HttpError as error:
        print(f"Error al acceder a Gmail API: {str(error)}")
        return {
            'status': 'error',
            'message': f'Error al acceder a Gmail API: {str(error)}'
        }
    except Exception as e:
        print(f"Error inesperado en get_emails_sent_to_client: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error inesperado: {str(e)}'
        }

def send_email_with_attachment(subject, html_body, recipient_email, recipient_name='', attachment_path=None, attachment_name=None):
    """
    Envía un correo electrónico con contenido HTML y archivo adjunto utilizando la API de Gmail.

    Args:
        subject (str): Asunto del correo.
        html_body (str): Contenido HTML del mensaje.
        recipient_email (str): Dirección de correo del destinatario.
        recipient_name (str): Nombre del destinatario (opcional).
        attachment_path (str): Ruta al archivo adjunto (opcional).
        attachment_name (str): Nombre del archivo adjunto (opcional).

    Returns:
        dict: Resultado del envío con 'status' y detalles adicionales.
    """
    try:
        # Obtén el servicio de Gmail
        service = GoogleService.get_service()['gmail']

        # Crear el mensaje con HTML
        message = MIMEMultipart()
        message['to'] = recipient_email
        message['from'] = "dcfenceapp@dcfence.org"
        message['subject'] = subject

        # Agregar el cuerpo HTML del mensaje
        html_part = MIMEText(html_body, 'html')
        message.attach(html_part)

        # Agregar archivo adjunto si se proporciona
        if attachment_path and attachment_name:
            with open(attachment_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment_name}'
            )
            message.attach(part)

        # Codificar el mensaje en base64url
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Enviar el mensaje
        send_message = (
            service.users()
            .messages()
            .send(userId='me', body={'raw': raw_message})
            .execute()
        )

        return {'status': 'success', 'messageId': send_message['id']}
    
    except HttpError as error:
        return {'status': 'error', 'message': str(error)}
    except Exception as e:
        return {'status': 'error', 'message': f"Unexpected error: {e}"}

def get_emails_by_date_range(client_email, start_date=None, end_date=None):
    """
    Extrae correos enviados a un cliente en un rango de fechas específico.
    
    Args:
        client_email (str): Dirección de correo del cliente.
        start_date (str): Fecha de inicio en formato 'YYYY/MM/DD'.
        end_date (str): Fecha de fin en formato 'YYYY/MM/DD'.
        
    Returns:
        dict: Resultado con correos filtrados por fecha.
    """
    try:
        service = GoogleService.get_service()['gmail']
        
        # Construir la consulta base
        query = f'to:{client_email}'
        
        # Agregar filtros de fecha si se proporcionan
        if start_date:
            query += f' after:{start_date}'
        if end_date:
            query += f' before:{end_date}'
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=100
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return {
                'status': 'success',
                'message': f'No se encontraron correos enviados a {client_email} en el rango de fechas especificado',
                'emails': []
            }
        
        # Procesar mensajes (similar a la función anterior)
        emails_details = []
        for message in messages:
            try:
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'Sin asunto')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')
                from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
                
                email_info = {
                    'id': message['id'],
                    'subject': subject,
                    'date': date,
                    'from': from_header,
                    'snippet': msg.get('snippet', '')
                }
                
                emails_details.append(email_info)
                
            except Exception as e:
                print(f"Error al procesar mensaje {message['id']}: {str(e)}")
                continue
        
        return {
            'status': 'success',
            'message': f'Se encontraron {len(emails_details)} correos enviados a {client_email}',
            'emails': emails_details
        }
        
    except HttpError as error:
        print(f"Error al acceder a Gmail API: {str(error)}")
        return {
            'status': 'error',
            'message': f'Error al acceder a Gmail API: {str(error)}'
        }
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return {
            'status': 'error',
            'message': f'Error inesperado: {str(e)}'
        }



def extract_headers_from_raw(message):
    """
    Extrae los headers del mensaje raw de Gmail API.
    
    Args:
        message (dict): Mensaje raw de Gmail API
        
    Returns:
        dict: Headers del email
    """
    try:
        # Decodificar el mensaje raw
        raw_data = message.get('raw', '')
        if not raw_data:
            return {}
        
        # Decodificar de base64url
        decoded_data = base64.urlsafe_b64decode(raw_data + '=' * (-len(raw_data) % 4))
        email_message = email.message_from_bytes(decoded_data, policy=policy.default)
        
        # Extraer headers
        headers = {}
        for key, value in email_message.items():
            headers[key.lower()] = value
        
        return headers
        
    except Exception as e:
        print(f"Error extracting headers from raw: {str(e)}")
        return {}






def get_email_full_content(message_id):
    """
    Obtiene el contenido completo de un email específico incluyendo archivos adjuntos.
    """
    try:
        service = GoogleService.get_service()['gmail']
        msg = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()
        attachments = extract_attachments_metadata(msg['payload'])
        return {
            'id': message_id,
            'attachments': attachments
        }
    except Exception as e:
        print(f"Error obteniendo contenido completo del email {message_id}: {str(e)}")
        return None
