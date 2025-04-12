from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.http import JsonResponse
from io import BytesIO
from django.views.decorators.csrf import csrf_exempt
from googleapiclient.http import MediaIoBaseUpload
import json
from .models import (Project)
from django.shortcuts import get_object_or_404
import os

drive_id = '0AF4IswhouZv_Uk9PVA'

class DriveService:
    _service = None
    _creds = None

    @staticmethod
    def get_service():
        if DriveService._service is None:
            credentials_info = json.loads(os.getenv('GOOGLE_CREDENTIALS', '{}'))
            if 'private_key' in credentials_info:
                credentials_info['private_key'] = credentials_info['private_key'].replace("\\n", "\n")
            
            creds = Credentials.from_service_account_info(
                credentials_info,
                scopes=["https://www.googleapis.com/auth/drive"]
            )
            
                
            # Refrescar las credenciales si es necesario
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            DriveService._creds = creds
            DriveService._service = build('drive', 'v3', credentials=creds)
        
        return DriveService._service

@csrf_exempt
def get_folders_in_drive(request):
    if request.method == 'POST':
        project_name = request.POST.get('project_name')
        
        if not project_name:
            return JsonResponse({'error': 'El nombre del proyecto es necesario'}, status=400)

        service = DriveService.get_service()  # Asegúrate de implementar esta función para autenticar tu servicio
        parent_folder_id = '0AF4IswhouZv_Uk9PVA'
        
        def fetch_children(folder_id):
            """Recursivamente obtiene los elementos hijos de una carpeta."""
            try:
                query = f"'{folder_id}' in parents and trashed = false"
                results = service.files().list(
                    corpora='drive', 
                    driveId=parent_folder_id, 
                    q=query,
                    fields="files(id, name, mimeType)",
                    includeItemsFromAllDrives=True,
                    supportsAllDrives=True
                ).execute()
                files = results.get('files', [])
                structure = []
                for file in files:
                    if file['mimeType'] == 'application/vnd.google-apps.folder':
                        structure.append({
                            "id": file['id'],
                            "name": file['name'],
                            "type": "folder",
                            "children": fetch_children(file['id'])  # Recursividad para obtener subcarpetas
                        })
                    else:
                        structure.append({
                            "id": file['id'],
                            "name": file['name'],
                            "type": "file",
                            "url": f"https://drive.google.com/file/d/{file['id']}"
                        })
                return structure
            except HttpError as error:
                return []

        try:
            # Buscar la carpeta del proyecto
            query = f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and name = '{project_name}' and trashed = false"
            results = service.files().list(
                corpora='drive', 
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
                    "type": "folder",
                    "children": fetch_children(folder['id'])
                })

            return JsonResponse({"message": "Estructura obtenida con éxito", "structure": structure})

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

            service = DriveService.get_service()
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
        
            service = DriveService.get_service()
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
        service = DriveService.get_service()

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

        service = DriveService.get_service()
        folder = service.files().create(
            body=file_metadata,
            fields='id, name',
            supportsAllDrives=True 
        ).execute()

        subfolders = [
            'Contract-SOV', 'Invoices', 'ChangeOrder',
            'Permit', 'Documents', 'Drawings', 
            'Proposal', 'Evidence'
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
        print(folder_root_value)
        service = DriveService.get_service()
        file_metadata = {'trashed': True}
        service.files().update(fileId=folder_root_value, body=file_metadata, supportsAllDrives=True).execute()
        return {
            'status': 'success',
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def upload_file_to_drive(request):
    if request.method == 'POST':
        try:
            service = DriveService.get_service()
            files = request.FILES.getlist('file[]')
            folder_id = request.POST.get('folder_id')

            file_ids = []
            for file in files:
                file_metadata = {
                    'name': file.name,
                    'parents': [folder_id]
                }
                
                media = MediaIoBaseUpload(file.file, mimetype=file.content_type)
                
                try:
                    file_uploaded = service.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id',
                        supportsAllDrives=True
                    ).execute()
                    file_ids.append(file_uploaded['id'])
                except HttpError as error:
                    print(f"Failed to upload {file.name}: {error}")
                    continue

            return JsonResponse({'message': 'Files uploaded successfully', 'file_ids': file_ids})
        
        except Exception as e:
            return JsonResponse({'message': f'Error occurred: {str(e)}'}, status=500)

    return JsonResponse({'message': 'Method not allowed'}, status=405)

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
        service = DriveService.get_service()
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
        print(folder_id)
        service = DriveService.get_service()
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