from pathlib import Path
from zipfile import ZipFile
import os
import magic
import mimetypes
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(name)s - [%(levelname)s] - %(message)s')

file_handler = logging.FileHandler('FileToolsPlus.log', mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# stream_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
# logger.addHandler(stream_handler)


class FTool:

    def __init__(self, path):
        self.path = path

    def extract_zip(self):
        folder_path = self.path.parent
        file_name = self.path.name
        with ZipFile(file=folder_path, mode='r') as zip_folder:
            html_data = zip_folder.open(file_name)
            contents = html_data.read()
            return contents

    def get_media_type(self):
        if isinstance(self.path, str):
            verify_path = os.path.exists(self.path)
            if not verify_path:
                raise TypeError(
                    f'{self.path} is not a valid filepath. Please provide valid file paths only.')
            logger.info(f'Getting media type for {self.path}')
            check_by_suffix = mimetypes.guess_type(self.path)[0]
            check_by_sniffing = magic.from_file(self.path, mime=True)
            if check_by_suffix is None:
                logger.info(f'No file suffix found. Identifying file by sniffing alone: {check_by_sniffing}')
                return check_by_sniffing
            if check_by_suffix != check_by_sniffing:
                file_name = os.path.basename(self.path)
                suffix = os.path.basename(self.path).split(".")[1]
                raise Exception(f'Warning: {file_name} has a suffix that does not match its media type.\n'
                                f'{suffix} indicates media type is {check_by_suffix}.\n'
                                f'Sniffing indicates media type is {check_by_sniffing}')
            return check_by_sniffing

        if isinstance(self.path, list):
            logger.info(f'Getting media type for multiple files: {self.path}')
            results = [self.get_media_type(i) for i in self.path]
            logger.info(f'Media types: {results}')
            return results


class SheetFile(FTool):

    sheet_name = '[ENTER NAME]'
    html_file = sheet_name + '.html'
    download_folder = Path("~/Downloads")

    def __init__(self, spreadsheet_title: str):
        self.spreadsheet_title = spreadsheet_title
        self.path = Path(self.download_folder) / self.spreadsheet_title / self.html_file
        super().__init__(self.path)

    def soupify_sheet(self):
        sheet_html = super().extract_zip()
        sheet_soup = BeautifulSoup(sheet_html, features='lxml')
        return sheet_soup

