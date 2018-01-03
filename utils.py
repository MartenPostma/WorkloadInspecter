import pandas
import seaborn as sns
from datetime import datetime
import matplotlib.pyplot as plt


def get_range_range(start, end, debug=False):
    """
    given two datetime.time objects (representing dates)
    compute the range between them:
    a) including start date
    b) including end date

    :param datetime.datetime start: datetime object
    :param datetime.datetime end: datetime object
    :param bool debug: 0 | 1 | 2

    :rtype: list
    :return: list of datetime.datetime objects
    """
    dt_objs = []

    delta = end - start

    if debug:
        print(f'num days between {start} and {end}: {delta.days}')

    if all([debug,
            delta.days < 0]):
        print(f'{end} before {start}')

    datelist = pandas.date_range(start, periods=delta.days + 1)

    for date in datelist:
        dt_objs.append(date.to_pydatetime())

    return dt_objs


# normal example
out_assert_1 = [datetime(2018, 1, 8),
                datetime(2018, 1, 9),
                datetime(2018, 1, 10)]
assert get_range_range(datetime(2018, 1, 8),
                       datetime(2018, 1, 10), debug=False) == out_assert_1
# same date as start and end example
assert get_range_range(datetime(2018, 1, 8),
                       datetime(2018, 1, 8), debug=False) == [datetime(2018, 1, 8)]

# start date before end date
assert get_range_range(datetime(2018, 1, 9),
                       datetime(2018, 1, 8), debug=False) == []


def load_holidays(info_df):
    """
    load set of holiday identifiers

    :param pandas.core.frame.DataFrame info_df: all date info

    :rtype: set
    :return set of datetime.datetime objects
    """
    holidays = set()

    for index, row in info_df.iterrows():
        date_range = get_range_range(row['from'],
                                     row['to'])

        for date in date_range:
            holidays.add(date)

    return holidays


class WorkLoadInspecter:
    """
    class to analyze workload over given period

    :ivar str path_to_input_excel: path to excel with information
    about work and holidays (see 'resources' folder for examples)
    :ivar dict i_work_on: dictionary mapping every weekday to True or False
    indicating whether you work on that day, e.g.
    input_i_work_on = {
        'Monday': True,
        'Tuesday' : False,
        'Wednesday': True,
        'Thursday': True,
        'Friday': True,
        'Saturday': False,
        'Sunday': False,
    }
    """

    def __init__(self, path_to_input_excel,
                 i_work_on):
        self.info_df = pandas.read_excel(path_to_input_excel, sheetname='work')
        self.holidays_df = pandas.read_excel(path_to_input_excel, sheetname='holidays')
        self.i_work_on = i_work_on
        self.int2day = {
            0: 'Monday',
            1: 'Tuesday',
            2: 'Wednesday',
            3: 'Thursday',
            4: 'Friday',
            5: 'Saturday',
            6: 'Sunday',
        }
        self.activity2date2int, self.all_dates = self.load_data()

    def my_upcoming_deadlines(self):
        """
        show deadlines (sorted by deadline date):
        a. holidays are excluded
        b. non-working days are excluded

        :rtype: pandas.core.frame.DataFrame
        :return: df with deadline information
        """
        list_of_lists = []
        headers = ['Activity', 'Deadline', '# working days remaining']

        for index, row in self.info_df.iterrows():

            if not row['deadline']:
                continue

            what = row['what']
            num_days_remaining = len(self.activity2date2int[what])
            a_row = [what, row['to'], num_days_remaining]
            list_of_lists.append(a_row)

        deadlines_df = pandas.DataFrame(list_of_lists, columns=headers)
        sorted_deadlines_df = deadlines_df.sort_values('Deadline')
        return sorted_deadlines_df

    def what_am_i_doing_during(self, from_date, to_date):
        """
        show activities during period from_date to_date

        :param str from_date: yyyy-mm-dd 2018-1-1
        :param str to_date: yyy-mm-dd 2018-1-3

        :rtype: pandas.core.frame.DataFrame
        :return: df with activities information
        """
        from_y, from_m, from_d = from_date.split('-')
        to_y, to_m, to_d = to_date.split('-')

        start = datetime(int(from_y), int(from_m), int(from_d))
        end = datetime(int(to_y), int(to_m), int(to_d))

        list_of_lists = []
        headers = ['Activity', 'From', 'To', '# working days remaining']

        for index, row in self.info_df.iterrows():

            what = row['what']

            if not any([start == row['from'],
                        start > row['from']
                        ]):
                continue

            if not any([end == row['to'],
                        end < row['to']
                        ]):
                continue

            num_days_remaining = len(self.activity2date2int[what])
            a_row = [what, row['from'], row['to'], num_days_remaining]
            list_of_lists.append(a_row)

        activities_df = pandas.DataFrame(list_of_lists, columns=headers)
        sorted_activities_df = activities_df.sort_values('To')
        return sorted_activities_df

    def visualize_my_activities(self, debug=False):
        """
        visualize all activities with stripplot

        a) the plot is shown in a notebook
        b) the plot is saved to 'output/overview.png'

        :rtype: matplotlib.axes._subplots.AxesSubplot
        :return: the plot (output of sns.stripplot)
        """
        list_of_lists = []
        headers = ['activity', 'date']

        for activity, activity_info in self.activity2date2int.items():

            for date in activity_info:
                a_row = [activity, date]
                list_of_lists.append(a_row)

        df = pandas.DataFrame(list_of_lists, columns=headers)

        sns.set_context(rc={"figure.figsize": (10, 5)})
        g = sns.stripplot(x="activity", y="date", data=df)
        plt.xticks(rotation=90)

        plt.savefig('output/overview.png')

        if debug:
            print('plot is saved to output/overview.png')

        return g

    def load_data(self):
        """
        compute two things:

        a) activity2date2int
        create for each activity a mapping from
        date to identifier

        b) all_dates
        sorted list of all dates

        :rtype: tuple
        :return: (activity2date2int, all_dates)
        """
        holidays = load_holidays(self.holidays_df)
        activity2date2int = {}
        all_dates = set()

        for index, row in self.info_df.iterrows():

            id_ = index + 1
            what = row['what']

            activity2date2int[what] = {}
            date_range = get_range_range(row['from'],
                                         row['to'])

            for date in date_range:

                int_day = date.weekday()
                day = self.int2day[int_day]
                if not self.i_work_on[day]:
                    continue

                all_dates.add(date)

                if date in holidays:
                    continue

                activity2date2int[what][date] = id_

        return activity2date2int, sorted(all_dates)
