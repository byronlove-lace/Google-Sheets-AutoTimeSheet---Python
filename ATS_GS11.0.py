import logging
import datetime
import pyinputplus as pyip
from GTools import GoogleServices
from DriveTools import DriveSearch
from SheetToolsPlus import Mapper, MapNav
from FileToolsPlus import SheetFile
from ATS_Tools_PlusPlusPlus import ClassTime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s: %(name)s - [%(levelname)s] - %(message)s')

file_handler = logging.FileHandler('ATS_GS11.0.log', mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# stream_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
# logger.addHandler(stream_handler)

'''Functions'''


def transpose(list_matrix):
    transposed_list = []

    for i in range(len(list_matrix[0])):
        row = []
        for item in list_matrix:
            row.append(item[i])
        transposed_list.append(row)

    return transposed_list


def ask_class_name():
    name = pyip.inputStr(prompt='Please enter class name: ')
    return name


initialize_sheets = GoogleServices(
    api_name='sheets', api_version='v4',
    client_secrets_path='client_secret_mds.json',
    token_path='token.json',
    scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
)

initialize_drive = GoogleServices(
    api_name='drive', api_version='v3',
    client_secrets_path='client_secret_mds.json',
    token_path='token.json',
    scopes=['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
)

sheets_service = initialize_sheets.create_service()
drive_service = initialize_drive.create_service()

class_time = ClassTime()
titles = class_time.gen_titles()
spreadsheet_title = titles[0]

try:
    spreadsheet = DriveSearch(query=titles[0], service_object=drive_service)
    spreadsheet.download_file(export_to='application/zip')
except FileNotFoundError:
    spreadsheet = DriveSearch(query=titles[1], service_object=drive_service)
    spreadsheet.download_file(export_to='application/zip')
    if spreadsheet:
        spreadsheet_title = titles[1]

logger.debug(f"spreadsheet_title: {spreadsheet_title}")
spreadsheet_id = DriveSearch(query=spreadsheet_title, service_object=drive_service).get_id()
sheet_html = SheetFile(spreadsheet_title=spreadsheet_title)
sheet_soup = sheet_html.soupify_sheet()
sheet_map = Mapper(sheet_soup=sheet_soup)
sheet_map = sheet_map.map_to_cells()
sheet_data = MapNav(sheet_map)
initial_cell_values = sheet_data.get_values()
first_input_cell = sheet_data.get_input_cell()

"This could be encapsulated in Drive_Tools"

class_name = ask_class_name()
ft_hours = class_time.ask_class_times()
st = ft_hours[0]
et = ft_hours[1]
hours_worked = class_time.find_working_hours(st, et)

st_formatted = datetime.datetime.strftime(st, '%H:%M')
et_formatted = datetime.datetime.strftime(et, '%H:%M')

if st_formatted.startswith('0'):
    st_formatted = st_formatted[1:]

if et_formatted.startswith('0'):
    et_formatted = et_formatted[1:]

logger.debug(f"start_time: {st_formatted}")
logger.debug(f"end_time: {et_formatted}")

working_dates = class_time.find_working_dates()
workday_count = len(working_dates)
logger.debug(f"workday_count = {workday_count}")
notes = None

base_values = [class_name, st_formatted, et_formatted, notes, hours_worked]
logger.debug(f"base_values = {base_values}")
scaled_values = [[i for k in range(workday_count)] for i in base_values]
scaled_values.insert(1, working_dates)
logger.debug(f"scaled_values = {scaled_values}")
added_cell_values = transpose(scaled_values)
logger.debug(f"Added cell vals: {added_cell_values}")
input_data = initial_cell_values + added_cell_values
logger.debug(f"input_data_with_dups: {input_data}")
logger.info(f"Length of total input before removing duplication: {len(input_data)}")

input_sans_duplicates = []
for i in input_data:
    if i not in input_sans_duplicates:
        input_sans_duplicates.append(i)
logger.info(f"Length of total input after removing duplication: {len(input_sans_duplicates)}")
for i, v in enumerate(input_sans_duplicates):
    if isinstance(v[1], str):
        input_sans_duplicates[i][1] = class_time.convert_date_to_dt(v[1])
logger.debug(f"input_sans_dups: {input_sans_duplicates}")

'''
ERRRRRROOOOOOORRRRRR: Debug and Finish
'''

logger.debug(f"input_sans_duplicates: {input_sans_duplicates}")
logger.debug(f"date_check: {type(input_sans_duplicates[0][1])}")
input_sans_duplicates.sort(key=lambda x: x[1])
input_sorted = input_sans_duplicates
for i in input_sorted:
    i[1] = datetime.datetime.strftime(i[1], "%d/%m/%Y")
logger.debug(f"input_sorted: {input_sorted}")

input_sorted = [tuple(i) for i in input_sorted]
input_sorted = tuple(input_sorted)
input_sorted_count = len(input_sorted)

input_body = {
    'majorDimension': 'ROWS',
    'values': input_sorted,
}


sheets_service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    valueInputOption='USER_ENTERED',
    range=SheetFile.sheet_name + "!" + first_input_cell,
    body=input_body
).execute()


spreadsheet_id = DriveSearch(query=spreadsheet_title, service_object=drive_service).get_id()
sheet_html = SheetFile(spreadsheet_title=spreadsheet_title)
sheet_soup = sheet_html.soupify_sheet()
sheet_map = Mapper(sheet_soup=sheet_soup)
sheet_map = sheet_map.map_to_cells()
sheet_data = MapNav(sheet_map)
initial_cell_values = sheet_data.get_values()
first_input_cell = sheet_data.get_input_cell()

clear_from, empty_cells = sheet_data.clear_cells(sorted_input_count=input_sorted_count)

if empty_cells:
    clear_body = {
        'majorDimension': 'COLUMNS',
        'values': empty_cells,
    }

    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        valueInputOption='USER_ENTERED',
        range=SheetFile.sheet_name + "!" + clear_from,
        body=clear_body
    ).execute()
