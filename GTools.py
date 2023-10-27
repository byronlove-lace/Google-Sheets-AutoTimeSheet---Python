import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

''' Logging Config.'''

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(name)s - [%(levelname)s] - %(message)s')

file_handler = logging.FileHandler('GTools.log', mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# stream_handler.setLevel(logging.INFO)

logger.addHandler(file_handler)
# logger.addHandler(stream_handler)


'''
The ideal solution that I should aim for here is to convert authorize into a wrapper
Not an instance method wrapper (which makes no sense, as the point of a wrapper is 
to add additional functionality, not to be a method in and of itself)
However, wrappers/decorators are going to take some time to master
    - particularly in the context of using them in classes (which I have only just 
    started doing)
As such, it may be best to hardcode the auth for now and wrap later

'''


class GoogleServices:
    def __init__(self,
                 api_name: str,
                 api_version: str,
                 scopes: str | list,
                 client_secrets_path: str,
                 token_path: str,
                 credentials=None,
                 ):

        # scopes repr?

        self.scopes = scopes
        self.credentials = credentials
        self.token_path = token_path
        self.client_secrets_path = client_secrets_path
        self.api_name = api_name
        self.api_version = api_version

    def __authorize(self):
        if os.path.exists(self.token_path):
            self.credentials = Credentials.from_authorized_user_file(self.token_path, self.scopes)
            logger.info('Token Found')
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                logger.info('Token Expired. Refreshing Token.')
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_path, self.scopes)
                self.credentials = flow.run_local_server(port=0)
                logger.info('Token not found. Requesting new token.')
            with open(self.token_path, 'w') as token:
                token.write(self.credentials.to_json())
                logger.info('Creating new token.')

    def create_service(self):
        self.__authorize()
        try:
            service = build(serviceName=self.api_name, version=self.api_version, credentials=self.credentials)
            logger.info('Service created successfully')
            return service
        except Exception as e:
            print('Unable to connect.')
            print(e)
            return None


class GoogleSheets:
    def __init__(self):
        pass

class GoogleDrive:
    def __init__(self):
        pass

