from GTools import GoogleServices
import logging
import pickle
import json
import pyinputplus as pyip
import io
import os
import mimetypes
import magic
from pathlib import Path
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import Resource

''' Logging Config.'''

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s: %(name)s - [%(levelname)s] - %(message)s')

file_handler = logging.FileHandler('DriveTools.log', mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# stream_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
# logger.addHandler(stream_handler)


'''
TODO:
    Test Secondary features 
    Tidy sheet functions into SheetTools.py classes - add searchbyval to this
    Tag on Frontend
       
        
Improvements:
    request json on files to upload is ambiguous
    duplication should not raise error for downloads (it should log notice and download both) 
    DriveUpload is still v LBYL

Considerations:
    should getId have fuzzyfind functionality?
        -> In general, yes. Though it isn't necessary for this project.
'''


class DriveSearch:

    mime_path = Path('~/PycharmProjects/GoogleSheets/mediatypes.txt')
    with mime_path.open('r') as f:
        media_types = f.readlines()
    media_types = [i.strip('\n') for i in media_types]

    def __init__(self, query: str, service_object: Resource):
        self.query = query
        self.service_object = service_object

    def get_id(self):
        # make a class function?
        drive_metadata = self.service_object.files().list().execute()
        all_file_metadata = drive_metadata.get('files')
        target_files = []
        for i in all_file_metadata:
            if i.get('name') == self.query:
                target_files.append(i)

        if len(target_files) < 1:
            raise FileNotFoundError('No files found.')

        if len(target_files) == 1:
            logger.info(f'File found: {target_files[0]}')
            target_id = target_files[0].get('id')
            return target_id

        if len(target_files) > 1:
            file_types = [i.get('mimeType') for i in target_files]
            types_sans_duplicates = set(file_types)
            if len(file_types) > len(types_sans_duplicates):
                logger.debug(f'Number of file types found: {str(len(file_types))}')
                logger.debug(f'Number of duplicates: {str(len(file_types) - len(types_sans_duplicates))}')
                raise Exception('Duplicates of file found. Please remove duplicates before continuing.')

            else:
                mime_of_download = pyip.inputMenu(choices=file_types,
                                                  prompt='Multiple files with this name found.\n'
                                                  'Please choose the type of the file you want to download:\n',
                                                  numbered=True)
                for i in target_files:
                    if i.get('mimeType') == mime_of_download:
                        target_id = i.get('id')

                        return target_id

    def download_file(self, export_to=None, download_destination=None):

        if export_to:
            assert export_to in self.media_types, 'export_to argument must be a str of a mime type.'

        if download_destination:
            assert Path(download_destination).is_dir(), 'download_destination must be a directory.'
            assert Path(download_destination).absolute(), 'download_destination must be an absolute path.'

        target_id = self.get_id()

        if export_to:
            request = self.service_object.files().export(fileId=target_id, mimeType=export_to)
        else:
            request = self.service_object.files().get_media(fileId=target_id)

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(fd=buffer, request=request)

        done = False

        while not done:
            status, done = downloader.next_chunk()
            progress = status.progress() * 100
            print(f'Download Progress: {progress}')

        buffer.seek(0)

        if not download_destination:
            download_destination = '~/Downloads'

        if download_destination.endswith('/'):
            download_destination = download_destination[:-1]

        path = Path(download_destination) / self.query
        path_type = str(type(path))
        logger.debug(f'Download path is a {path_type}')
        with path.open(mode='wb') as f:
            f.write(buffer.read())


class DriveUpload:

    def __init__(self, service_object: Resource, files_to_upload: (str | list), destination=None, request_json=None):

        self.files_to_upload = files_to_upload
        self.destination = destination
        self.request_json = request_json
        self.service_object = service_object

    def get_media_type(self):
        if isinstance(self.files_to_upload, str):
            verify_path = os.path.exists(self.files_to_upload)
            if not verify_path:
                raise TypeError(f'{self.files_to_upload} is not a valid filepath. Please provide valid file paths only.')
            logger.info(f'Getting media type for {self.files_to_upload}')
            check_by_suffix = mimetypes.guess_type(self.files_to_upload)[0]
            check_by_sniffing = magic.from_file(self.files_to_upload, mime=True)
            if check_by_suffix is None:
                logger.info(f'No file suffix found. Identifying file by sniffing alone: {check_by_sniffing}')
                return check_by_sniffing
            if check_by_suffix != check_by_sniffing:
                file_name = os.path.basename(self.files_to_upload)
                suffix = os.path.basename(self.files_to_upload).split(".")[1]
                raise Exception(f'Warning: {file_name} has a suffix that does not match its media type.\n'
                                f'{suffix} indicates media type is {check_by_suffix}.\n'
                                f'Sniffing indicates media type is {check_by_sniffing}')
            return check_by_sniffing

        if isinstance(self.files_to_upload, list):
            logger.info(f'Getting media type for multiple files: {self.files_to_upload}')
            results = [self.get_media_type(i) for i in self.files_to_upload]
            logger.info(f'Media types: {results}')
            return results

    def upload_files(self):

        folder_id = None
        file_mime = None
        upload_metadata = None

        if self.destination:
            logger.info(f'GDrive self.destination folder: {self.destination}')
            search_query = DriveSearch(query=self.destination, service_object=self.service_object)
            folder_id = search_query.get_id()
            logger.info(f'Folder ID: {folder_id}')

        upload_mimes = self.get_media_type()

        if isinstance(self.files_to_upload, str):
            file_mime = (self.files_to_upload, upload_mimes)
        if isinstance(self.files_to_upload, list):
            file_mime = list(zip(self.files_to_upload, upload_mimes))

        if self.request_json:
            if isinstance(self.request_json, str):
                if Path(self.request_json).exists():
                    if magic.from_file(self.request_json, mime=True) == 'data':
                        with open(self.request_json, 'rb') as f:
                            upload_metadata = pickle.load(f)
                    if magic.from_file(self.request_json, mime=True) == 'application/json':
                        with open(self.request_json, 'rb') as f:
                            upload_metadata = json.load(f)

            if isinstance(self.request_json, dict):
                upload_metadata = self.request_json

        else:
            upload_metadata = {
                'name': None,
                'mimeType': None,
                'parents': None
            }

        if isinstance(file_mime, tuple):
            upload_metadata['name'] = os.path.basename(file_mime[0])
            upload_metadata['mimeType'] = file_mime[1]
            upload_metadata['parents'] = [folder_id]

            media = MediaFileUpload(self.files_to_upload, mimetype=file_mime[1])

            self.service_object.files().create(
                body=upload_metadata,
                media_body=media,
                fields='id'
            ).execute()

        if isinstance(file_mime, list):
            for i, v in enumerate(file_mime):
                upload_metadata['name'] = os.path.basename(v[0])
                upload_metadata['mimeType'] = v[1]
                upload_metadata['parents'] = [folder_id]

                media = MediaFileUpload(self.files_to_upload[i], mimetype=v[1])

                self.service_object.files().create(
                    body=upload_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

