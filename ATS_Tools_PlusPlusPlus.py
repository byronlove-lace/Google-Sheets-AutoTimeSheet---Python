import datetime
import calendar
import logging
import exrex
import pyinputplus as pyip

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s: %(name)s - [%(levelname)s] - %(message)s')

file_handler = logging.FileHandler('ATS_Tools.log', mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)
# stream_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
# logger.addHandler(stream_handler)
'''Backend'''


class ClassTime:

    date_formats = list(exrex.generate(r'^(%d)(/(%m|%b|%B)/|-(%m|%b|%B)-|\.(%m|%b|%B)\.)(%y|%Y)$'))

    st_morning = datetime.time(hour=8, minute=30)
    et_morning = datetime.time(hour=11)

    st_afternoon = datetime.time(hour=13, minute=30)
    et_afternoon = datetime.time(hour=16)

    def __init__(self):

        today = datetime.date.today()
        month = today.month
        l_month = month - 1
        day = today.day
        if day >= 26:
            l_month = month
            month = month + 1
        year = today.year
        pay_month_start = datetime.datetime(year=year, month=l_month, day=27)
        pay_month_end = datetime.datetime(year=year, month=month, day=26)

        self.today = today
        self.month = month
        self.l_month = l_month
        self.day = day
        self.year = year
        self.pay_month_start = pay_month_start
        self.pay_month_end = pay_month_end

    def convert_date_to_dt(self, date):

        for i in self.date_formats:
            try:
                dt_obj = datetime.datetime.strptime(date, i)

                return dt_obj

            except ValueError:
                continue

    def gen_titles(self):

        year = str(self.year)[-2:]
        year = int(year)

        spreadsheet_title = f"Teaching time FINAL TEST (27.{self.l_month}.{year}-26.{self.month}.{year})"
        alt_title = f"Teaching time FINAL TEST (27.{self.l_month}-26.{self.month}.{year})"

        return spreadsheet_title, alt_title

    def ask_from_to_dates(self):

        print('Please enter starting and ending dates of the class below. \n'
              'Leave input blank if start or end date takes place outside  month.\n'
              'Enter the same date for both if class is a one off.')

        from_date = pyip.inputDate(prompt='Please enter class starting date: ', formats=self.date_formats, blank=True)
        if from_date == '':
            from_date = self.pay_month_start
        to_date = pyip.inputDate(prompt='Please enter class ending date: ', formats=self.date_formats, blank=True)
        if to_date == '':
            to_date = self.pay_month_end

        return [from_date, to_date]

    @staticmethod
    def ask_working_days():

        day_names_full = list(calendar.day_name)
        day_names_abrvs = list(calendar.day_abbr)
        day_variations = dict(zip(day_names_full, day_names_abrvs))

        workdays = pyip.inputStr(prompt="Please enter the name of the days you'll be working: ")
        if ',' in workdays:
            workdays = workdays.split(',')
            workdays = [i.strip() for i in workdays]
        else:
            workdays = workdays.split(' ')

        workdays = [i for i in workdays if i != '']

        workdays_formatted = []

        for i in workdays:
            if i.title() in day_variations.keys():
                workdays_formatted.append(i.title())
            if i.title() in day_variations.values():
                [workdays_formatted.append(k) for k, v in day_variations.items() if v == i.title()]

        return workdays_formatted

    def find_working_dates(self):
        start_dt, end_dt = self.ask_from_to_dates()
        start_dt = datetime.datetime.combine(start_dt, datetime.time.min)
        end_dt = datetime.datetime.combine(end_dt, datetime.time.min)
        logger.debug(f"start_date, end_date: {start_dt}, {end_dt}")

        if start_dt == end_dt:
            return [start_dt]

        workdays = self.ask_working_days()
        day_delta = datetime.timedelta(days=1)
        date_range = (end_dt - start_dt).days
        logger.debug(f"date_range: {date_range}")

        dates = []

        for i in range(date_range + 1):
            date = start_dt + i * day_delta
            logger.debug(f"date: {date}")
            if date.strftime('%A') in workdays:
                dates.append(date)

        logger.debug(f"dates: {dates}")
        return dates

    def ask_class_times(self):

        class_times = []

        class_time_choice = pyip.inputMenu(
            ['Usual morning slot', 'Usual afternoon slot', 'Custom time'],
            prompt='Please choose class time:\n',
            numbered=True)

        if class_time_choice == 'Usual morning slot':
            class_times = self.st_morning, self.et_morning

        if class_time_choice == 'Usual afternoon slot':
            class_times = self.st_afternoon, self.et_afternoon

        if class_time_choice == 'Custom time':
            time_formats = ['%H:%M', '%I:%M%p', '%H.%M', '%I.%M%p']
            st_custom = pyip.inputTime(prompt='Please input start time: ', formats=time_formats)
            et_custom = pyip.inputTime(prompt='Please input end time: ', formats=time_formats)
            class_times = st_custom, et_custom

        class_times = [datetime.datetime.combine(datetime.date.min, i) for i in class_times]

        return class_times

    @staticmethod
    def find_working_hours(start_time, end_time):
        class_time = end_time - start_time
        class_time_hours = class_time.seconds / 3600

        return class_time_hours


class TimeSort:
    def __init__(self, start_time, end_time):
        self.start_time = start_time
        self.end_time = end_time

    @staticmethod
    def convert_time_to_dt(hour_minutes):
        # could account for different time formats

        time_formats = ['%H:%M', '%I:%M%p', '%H.%M', '%I.%M%p']

        for i in time_formats:
            try:
                dt_obj = datetime.datetime.strptime(hour_minutes, i)

                return dt_obj

            except ValueError:
                continue

    def find_working_hours(self):
        class_time = self.end_time - self.start_time
        class_time_hours = class_time.seconds / 3600

        return class_time_hours


