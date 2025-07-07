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
        print(f"Error al listar archivos en la carpeta: {e}")
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
import base64

def send_email(subject, html_body, recipient_email):
    """
    Envía un correo electrónico con contenido HTML utilizando la API de Gmail.

    Args:
        subject (str): Asunto del correo.
        html_body (str): Contenido HTML del mensaje.
        recipient_email (str): Dirección de correo del destinatario.

    Returns:
        dict: Resultado del envío con 'status' y detalles adicionales.
    """
    try:
        # Obtén el servicio de Gmail (asegúrate de que esté correctamente implementado)
        service = GoogleService.get_service()['gmail']

        # Crear el mensaje con HTML
        message = MIMEText(html_body, 'html')  # Ahora el mensaje es HTML
        message['to'] = recipient_email
        message['from'] = "tu_correo@gmail.com"  # Configura correctamente tu correo remitente
        message['subject'] = subject

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
