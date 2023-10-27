from pathlib import Path
import zipfile
from bs4 import BeautifulSoup
from openpyxl.utils import column_index_from_string
from bs4.element import Tag
import logging
from string import ascii_uppercase
import itertools
import numpy as np

'''
TODO: 
Convert to func
Fix Output

TOCONSIDER:
Make use of classes. This could be done by making the html the input for the class object.

FUTURE IMPROVEMENT:
    This search function could be improved with an implementation of pidgeonhole sorting 

NOTE FOR FUTURE PROJECTS:
    funcs will use under_line
    classes will use TitleCase
'''

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s: %(name)s - [%(levelname)s] - %(message)s')

file_handler = logging.FileHandler('SheetTools.log', mode='w')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# stream_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
# logger.addHandler(stream_handler)


class Mapper:

    def __init__(self, sheet_soup):
        self.sheet_soup = sheet_soup

    @staticmethod
    def __find_specific_att_value(target: Tag, attr: str):
        try:
            att_val = target[attr]
            return att_val
        except KeyError:
            return None

    @staticmethod
    def __find_specific_children(parent: Tag, child: str):
        all_children = parent.children
        specific_children = [i for i in all_children if i.name == child]
        return specific_children

    @staticmethod
    def __generate_empty_sheet():
        col_letters = list(ascii_uppercase)
        nums = [i for i in range(1, 1001)]

        cells_a1 = list(itertools.product(col_letters, nums))
        cells_a1.sort(key=lambda x: x[1])
        cells_a1 = [[i[0] + str(i[1]), 'unset_value', 'unset_state'] for i in cells_a1]
        cells_a1 = np.array(cells_a1, dtype=object)

        cells_a1_ordered = np.reshape(cells_a1, (1000, 26, 3))
        return cells_a1_ordered

    @classmethod
    def __find_width_of_sheet(cls, row_of_cells):
        colspan_total = []
        for cell in row_of_cells:
            colspan = cls.__find_specific_att_value(target=cell, attr='colspan')
            if colspan:
                colspan_total.append(int(colspan) - 1)
        return sum(colspan_total) + len(row_of_cells)

    def map_to_cells(self):

        tr_tags = self.sheet_soup.find_all('tr')
        del tr_tags[0]
        td_tags = [self.__find_specific_children(i, 'td') for i in tr_tags]
        max_row = len(tr_tags)
        max_col = self.__find_width_of_sheet(td_tags[0])
        sheet = self.__generate_empty_sheet()
        resized_sheet = sheet[:max_row, :max_col]
        row_counter = (i for i in range(0, max_row))

        for row in td_tags:
            rc = next(row_counter)
            col_counter = (i for i in range(0, max_col))
            if len(row) == 0:
                continue

            for n, cell in enumerate(row):
                cc = next(col_counter)

                while resized_sheet[rc, cc, 1] != 'unset_value':
                    cc = next(col_counter)

                content = cell.get_text()
                if not content:
                    content = 'Empty'

                horizontal_merge = self.__find_specific_att_value(target=cell, attr='colspan')
                vertical_merge = self.__find_specific_att_value(target=cell, attr='rowspan')

                if horizontal_merge or vertical_merge:
                    if horizontal_merge:
                        horizontal_merge = int(horizontal_merge) + cc
                        if horizontal_merge - cc == 1:
                            horizontal_merge += 1
                    else:
                        horizontal_merge = cc + 1
                    if vertical_merge:
                        vertical_merge = int(vertical_merge) + rc
                        if vertical_merge - rc == 1:
                            vertical_merge += 1
                    else:
                        vertical_merge = rc + 1

                    resized_sheet[rc:vertical_merge, cc:horizontal_merge, 1] = content
                    resized_sheet[rc:vertical_merge, cc:horizontal_merge, 2] = \
                        f'MERGE: {resized_sheet[rc, cc, 0]}:{resized_sheet[vertical_merge - 1, horizontal_merge - 1, 0]}'

                    col_counter = (i for i in range(horizontal_merge, max_col))

                else:
                    resized_sheet[rc, cc, 1] = content
                    resized_sheet[rc, cc, 2] = 'SINGLE'

        return resized_sheet


class MapNav:

    header_names = ['Class', 'Date', 'Start time', 'End time', 'Note', 'Hour']

    def __init__(self, sheet_map):
        self.sheet_map = sheet_map

    def __search_by_val(self, val):
        for row in self.sheet_map:
            for cell in row:
                if cell[1] == val:
                    return cell[0]

    def __get_parameters(self):

        header_cells = [self.__search_by_val(i) for i in self.header_names]
        header_cols = [i[0] for i in header_cells]
        header_row = int(header_cells[0][1])
        entry_row_ind = header_row

        first_header_ind = column_index_from_string(header_cols[0]) - 1
        last_header_ind = column_index_from_string(header_cols[-1])
        first_header_vals = self.sheet_map[entry_row_ind:, first_header_ind, 1]
        first_availible_row = np.where(first_header_vals == 'Empty')[0][0]
        availible_row_ind = first_availible_row + entry_row_ind
        first_input_cell = header_cols[0][0] + str(entry_row_ind + 1)

        parameters = [header_cols, entry_row_ind, availible_row_ind, first_header_ind, last_header_ind, first_input_cell]

        return parameters

    def get_values(self):

        header_cols, entry_row_ind, availible_row_ind, \
            first_header_ind, last_header_ind, first_input_cell = self.__get_parameters()

        initial_cell_values = self.sheet_map[entry_row_ind:availible_row_ind, first_header_ind:last_header_ind, 1]
        initial_cell_values = initial_cell_values.tolist()

        for row in initial_cell_values:
            for ind, val in enumerate(row):
                if val == 'Empty':
                    row[ind] = None

        return initial_cell_values

    def get_input_cell(self):
        parameters = self.__get_parameters()
        first_input_cell = parameters[-1]
        return first_input_cell

    def clear_cells(self, sorted_input_count: int):

        header_cols, entry_row_ind, availible_row_ind, \
            first_header_ind, last_header_ind, first_input_cell = self.__get_parameters()

        first_header_ind = column_index_from_string(header_cols[0]) - 1
        last_header_ind = column_index_from_string(header_cols[-1])
        logger.debug(f"last_header_index: {last_header_ind}")
        first_header_vals = self.sheet_map[entry_row_ind:, first_header_ind, 1]
        first_empty_row = np.where(first_header_vals == 'Empty')[0][0]

        logger.debug(f"first_empty_row: {first_empty_row}")
        rows_in_sheet = availible_row_ind - entry_row_ind
        logger.debug(f"rows_in_sheet: {rows_in_sheet}")
        num_rows_to_clear = rows_in_sheet - sorted_input_count
        logger.debug(f"num_rows_to_clear: {num_rows_to_clear}")
        if num_rows_to_clear > 0:
            clear_from_row = availible_row_ind - num_rows_to_clear + 1
            clear_to_row = clear_from_row + num_rows_to_clear
            logger.debug(f"clear_from_row: {clear_from_row}")
            clear_from_cell = header_cols[0] + str(clear_from_row)
            logger.debug(f"clear_from_cell: {clear_from_cell}")
            clear_to_cell = header_cols[-1] + str(clear_to_row)
            logger.debug(f"clear_to_cell: {clear_to_cell}")

            empty_cells = np.full(shape=(num_rows_to_clear, len(header_cols) + 1), fill_value='', dtype=object)
            empty_cells.tolist()
            return clear_from_cell, empty_cells
        else:
            return None, None
