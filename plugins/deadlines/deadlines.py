#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import getopt
import time
import datetime
import copy
import threading
import os.path
import shlex
import json
import pickle

from plugins.parsingplugintemplate import ParsingPluginTemplate

class deadline:
    def __init__(self, guid, when=None, info=None, users=None):
        #public readonly
        self.guid = guid

        #private
        self._users = set()
        self._when = datetime.datetime.now()
        self._info = ''
        
        if isinstance(when, datetime.datetime):
            self.set_datetime(when)
        elif when != None:
            try:
                self.set_datetime(datetime.datetime.strptime(when, '%c'))
            except:
                pass
        
        if info != None:
            self.set_info(info)
        
        if users != None:
            try:
                # try to use as iterable: https://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
                for user in users:
                    self.add_user(user)
            except:
                self.add_user(users)
    
    def set_datetime(self, dt):
        self._when = dt

    def set_date(self, _year, _month, _day):
        self._when = self._when.replace(year=_year, month=_month, day=_day)

    def set_time(self, _hour, _minute):
        self._when = self._when.replace(hour=_hour, minute=_minute)

    def get_datetime(self):
        return self._when

    def get_date(self):
        return self._when.year, self._when.month, self._when.day

    def get_time(self):
        return self._when.hour, self._when.minute

    def is_future(self, now=None):
        if now == None:
            now = datetime.datetime.now()

        return self._when > now

    def is_current_year(self):
        return self._when.year == datetime.datetime.now().year

    def set_info(self, info_text):
        self._info = info_text

    def get_info(self):
        return self._info if self._info != '' else 'No info'

    def add_user(self, user):
        self._users.add(user)

    def remove_user(self, user):
        self._users.remove(user)

    def get_users(self):
        return copy.deepcopy(self._users)

    def num_users(self):
        return len(self._users)
    
    def to_dict(self):
        return {'guid':self.guid, 'when':self._when.strftime('%c'), 'info':self._info, 'users':list(self._users)}
    
    @staticmethod
    def from_dict(obj):
        return deadline(obj['guid'], obj['when'], obj['info'], obj['users'])

class DeadlinesPlugin(ParsingPluginTemplate):
    """
    deadlines plugin

    usage:

        adding things:
            !deadlines (-a,  --add) <guid> [OPS]
                where <guid> is a unique ID for the deadline such as "adktenta"
                where [OPS] is an optional sequence of settings:
                    (-t,  --time) TIMESTR       set the time, e.g -t "15 jan 13:00"
                                                many formats are supported
                                                specifying date only or time only is allowed
                                                if you dont want to quote your arguments you can
                                                supply multiple -t options: -t 20170225 -t 22:00

                    (-i,  --info) TEXT          set arbitrary info text

                    (-j,  --join) USERNAME      add USERNAME to the deadline
                                                this option can be used multiple times for
                                                adding many users at once, e.g -j foo -j bar -j ...

                    (-d,  --done) USERNAME      remove USERNAME from the deadline
                                                this option can be used multiple times for
                                                removing many users at once, e.g -d foo -d bar -d ...

        changing existing things:
            !deadlines (-c,  --change) <guid> [OPS]
                where <guid> and [OPS] are identical to the above section on adding things.

        removing things:
            !deadlines (-r,  --remove) <guid>
                where <guid> is the unique ID for the deadline

        listing things:
            !deadlines [FILTER]
                where [FILTER] is an optional sequence of filter options:
                    (-n,  --num) N              set number of deadlines to include

                    (-p,  --past)               show past deadlines

                    (-w,  --who) USERNAME       only show deadlines to which USERNAME belongs
                                                can be used multiple times, e.g -w foo -w bar
    """
    def __init__(self, bot):
        super(DeadlinesPlugin, self).__init__(bot, command="deadlines", description="Handles a list of deadlines.")

        self.deadlines = []
        self.mutex = threading.Lock()
        self.filename = "{}deadlines.json".format(self._bot.get_base_data_path())
        
        self.disable_saving = False
        
        self.load()

    def paste(self, text, message):
        return self._bot.get_service("paste").paste(text, message)

    def add_deadline(self, guid):
        if self.get_deadline(guid) == None:
            self.deadlines.append(deadline(guid))
            return self.deadlines[-1]

    def get_deadline(self, guid):
        for entry in self.deadlines:
            if entry.guid == guid:
                return entry

        return None

    def remove_deadline(self, guid):
        deadline = self.get_deadline(guid)

        if deadline != None:
            self.deadlines.remove(deadline)
            return True
        else:
            return False

    def try_parse_datetime_using_formats(self, formats, text):
        dt = None

        now = datetime.datetime.now()
        current_year = int(now.year)
        next_year = current_year + 1

        for fmt in formats:
            try:
                dt = datetime.datetime.strptime(text, fmt[0])

                # year not included? set to current year
                if fmt[1] == False:
                    dt = dt.replace(year=current_year)

                # datetime in the past? set to next year
                if dt < now:
                    dt = dt.replace(year=next_year)

            except ValueError:
                # print('{} didnt match {}'.format(fmt, text))
                continue

        return dt

    def try_parse_datetime(self, text):
        formats = list()

        # [format, year_included]
        formats.append(['%Y%m%d %H:%M', True])
        formats.append(['%Y-%m-%d %H:%M', True])
        formats.append(['%d/%m %Y %H:%M', True])
        formats.append(['%d/%m %H:%M', False])
        formats.append(['%d %b %Y %H:%M', True])
        formats.append(['%d %b %H:%M', False])
        formats.append(['%b %d %Y %H:%M', True])
        formats.append(['%b %d %H:%M', False])

        return self.try_parse_datetime_using_formats(formats, text)

    def try_parse_date(self, text):
        formats = list()

        # [format, year_included]
        formats.append(['%Y%m%d', True])
        formats.append(['%Y-%m-%d', True])
        formats.append(['%d/%m %Y', True])
        formats.append(['%d/%m', False])
        formats.append(['%d %b %Y', True])
        formats.append(['%d %b', False])
        formats.append(['%b %d %Y', True])
        formats.append(['%b %d', False])

        return self.try_parse_datetime_using_formats(formats, text)

    def try_parse_time(self, text):
        return self.try_parse_datetime_using_formats([['%H:%M', False]], text)

    def save(self):
        if self.disable_saving == True:
            self.log('not saving because saving is disabled')
            return
        
        if self.deadlines == []:
            self.log('not saving an empty list of deadlines')
            return
        
        self.log('saving')
        
        outfile = open(self.filename, 'w+')
        json.dump(list(map(lambda x: x.to_dict(), self.deadlines)), outfile)
        outfile.close()

    def load(self):
        if os.path.isfile(self.filename):
            try:
                infile = open(self.filename, 'r')
                self.deadlines = list(map(deadline.from_dict, json.load(infile)))
                infile.close()
                
                self.log('loaded {} deadlines'.format(len(self.deadlines)))
            except Exception as e:
                self.log(str(e))
                self.disable_saving = True
                self.deadlines = []

    def format_printout(self, deadline):
        userlist = ','.join(list(deadline.get_users()))

        if deadline.is_current_year():
            return '({}) {}: {} [{}]'.format(deadline.guid,
             deadline.get_datetime().strftime('%a %d %b %H:%M'),
             deadline.get_info(),
             userlist if userlist != '' else '(empty)')
        else:
            return '({}) {}: {} [{}]'.format(deadline.guid,
             deadline.get_datetime().strftime('%a %d %b %Y %H:%M'),
             deadline.get_info(),
             userlist if userlist != '' else '(empty)')

    def pparse(self, message):
        self.log("Resut:" + str(self.parse(message)))

    def parse(self, message):
        if self.disable_saving == True:
            return 'Something is wrong with the deadlines data!'
        
        argv = shlex.split(message.get_text())

        try:
            opts, nonopts = getopt.getopt(argv, 'ha:c:t:i:j:d:r:n:pw:',
             ['help', 'add=', 'change=', 'time=', 'info=', 'join=', 'done=',
              'remove=', 'num=', 'past', 'who='])
        except:
            return 'What? Try --help'

        current_deadline = None

        response = []

        with self.mutex:
            try:
                for opt in opts:
                    if opt[0] == '-h' or opt[0] == '--help':
                        response = [DeadlinesPlugin.__doc__]
                        break
                    if opt[0] == '-a' or opt[0] == '--add':
                        if self.get_deadline(opt[1]) == None:
                            current_deadline = self.add_deadline(opt[1])
                            response.append('Deadline added')
                        else:
                            response.append('Deadline already exists')
                    elif opt[0] == '-c' or opt[0] == '--change':
                        current_deadline = self.get_deadline(opt[1])

                        if current_deadline == None:
                            response.append('No such deadline')
                    elif opt[0] == '-r' or opt[0] == '--remove':
                        if self.remove_deadline(opt[1]) == True:
                            response.append('Deadline removed')
                        else:
                            response.append('No such deadline')
                    elif current_deadline != None:
                        if opt[0] == '-t' or opt[0] == '--time':
                            dt_datetime = self.try_parse_datetime(opt[1])
                            dt_date = self.try_parse_date(opt[1])
                            dt_time = self.try_parse_time(opt[1])

                            if dt_datetime != None:
                                current_deadline.set_datetime(dt_datetime)
                                response.append('Date and time updated for {}'.format(current_deadline.guid))
                                continue
                            elif dt_date != None:
                                current_deadline.set_date(dt_date.year, dt_date.month, dt_date.day)
                                response.append('Date updated for {}'.format(current_deadline.guid))
                                continue
                            elif dt_time != None:
                                current_deadline.set_time(dt_time.hour, dt_time.minute)
                                response.append('Time updated for {}'.format(current_deadline.guid))
                                continue
                            else:
                                response.append('Did not understand your date/time')
                        elif opt[0] == '-i' or opt[0] == '--info':
                            current_deadline.set_info(opt[1])
                            response.append('Info updated for {}'.format(current_deadline.guid))
                        elif opt[0] == '-j' or opt[0] == '--join':
                            current_deadline.add_user(opt[1])
                            response.append('Added {} to {}'.format(opt[1], current_deadline.guid))
                        elif opt[0] == '-d' or opt[0] == '--done':
                            current_deadline.remove_user(opt[1])
                            response.append('Removed {} from {}'.format(opt[1], current_deadline.guid))

                if len(response) == 0:
                    if len(nonopts) > 0:
                        for arg in nonopts:
                            entry = self.get_deadline(arg)

                            if entry != None:
                                response.append(self.format_printout(entry))
                            else:
                                response.append('{}: No such deadline'.format(arg))
                    else:
                        stuff = sorted(self.deadlines, key=lambda x: x.get_datetime())

                        num = 3
                        past = False

                        for opt in opts:
                            if opt[0] == '-n' or opt[0] == '--num':
                                num = int(opt[1]) if opt[1].isdigit() else 3
                            elif opt[0] == '-p' or opt[0] == '--past':
                                past = True
                            elif opt[0] == '-w' or opt[0] == '--who':
                                stuff = list(filter(lambda x: opt[1] in x.get_users(), stuff))

                        if past == False:
                            stuff = list(filter(lambda x: x.is_future(), stuff))

                        for d in stuff[0:num]:
                            response.append(self.format_printout(d))
            except:
                response = [DeadlinesPlugin.__doc__]
            finally:
                self.save()

                if len(response) == 0:
                    return "No deadlines were found."

                ans = '\n'.join(response)

                return self.paste(ans, message)

