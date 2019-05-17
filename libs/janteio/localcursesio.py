#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import curses
import threading
import datetime
import traceback

import janteio.basicio
from jantemessage import JanteMessage

KEY_ESCAPE = '\x1b'
KEY_BACKSPACE = 263
KEY_LEFTARROW = 260
KEY_RIGHTARROW = 261
KEY_UPARROW = 259
KEY_DOWNARROW = 258
KEY_RETURN = '\n'

class LocalCursesIO(janteio.basicio.BasicIO):
    class errorRedirector():
        def __init__(self, IO):
            self._io = IO
        def write(self, data):
            self._io.error(data)
        def flush():
            pass
    
    
    def __init__(self, bot):
        super(LocalCursesIO, self).__init__(bot)
        self.output_buffer_mutex = threading.Lock()
        self.output_buffer = list()

        self.output_buffer.append('*** Press ESCAPE to exit this environment ***')
        self.output_buffer.append('')

        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()

        self.screen.clear()

        self.output_pane = curses.newwin(curses.LINES - 3, curses.COLS, 0, 0)
        self.output_pane.refresh() # draw

        self.input_pane = curses.newwin(3, curses.COLS, curses.LINES - 3, 0)
        self.input_pane.keypad(True) # makes it so special keys (like arrows) do not send escape sequences
        self.input_pane.refresh() # draw
        self.input_pane.timeout(25)

        self.input_origin = (1, 1)
        self.input_pos = (1, 1)
        self.input_text = ''

        self.input_history = list()
        self.input_history_current = ''
        self.input_history_pos = 0
        
        errorRedirector = LocalCursesIO.errorRedirector(self)

    def exit(self, quitmessage):
        sys.stderr.write("Exiting: " + quitmessage + "\n")
        #sys.stderr.flush()
        curses.nocbreak()
        self.screen.keypad(False)
        self.input_pane.keypad(False)
        curses.echo()
        curses.endwin()

    def send(self, message):
        with self.output_buffer_mutex:
            self.output_buffer.append("------------------------------------")
            self.output_buffer.append("Address:" + message.get_address())
            if not message.get_recipient() == "":
                self.output_buffer.append("RECIPIENT:" + message.get_recipient())
            if message.get_send_to_all():
                self.output_buffer.append("SENDALL:" + message.get_send_to_all())
            
            for line in ('CHAT:\n' + str(message.get_text()).strip()).split('\n'):
                self.output_buffer.append(line)
            
            self.output_buffer.append("------------------------------------")

    def recieve(self):

        try:
            self.input_pane.addstr(self.input_origin[0], self.input_origin[1], self.input_text) # redraw current input line

            try:
                key = self.input_pane.get_wch(self.input_pos[0], self.input_pos[1]) # get a unicode character from keyboard
            except:
                with self.output_buffer_mutex:
                    output_y = 1

                    for line in self.output_buffer[-(curses.LINES - 5):]:
                        self.output_pane.addstr(output_y, 1, ' ' * (curses.COLS - 2)) # visually erase line in output pane
                        self.output_pane.addstr(output_y, 1, line.replace('\n', ''))
                        output_y += 1

                    self.output_pane.box() # the boxes get broken sometimes
                    self.input_pane.box()

                    self.output_pane.refresh()
                    self.input_pane.refresh()

                return None

            if key == KEY_ESCAPE:
                self.exit("Exited due to keypress")
                # TODO: have basicIO have some facility of notifying users that IO
                # TODO: .. is closing / has been closed, and replace this hack with it
                #quit()
                return JanteMessage('QUIT', address='QUIT', sender='QUIT')
            elif key == KEY_BACKSPACE:
                if self.input_pos[1] > 1:
                    self.input_text = self.input_text[:-1] # chop off last char of input
                    self.input_pos = (self.input_pos[0], self.input_pos[1] - 1) # rewind input pos
                    self.input_pane.addstr(self.input_pos[0], self.input_pos[1], ' ') # visually erase char by drawing a space over it
                    self.input_pane.refresh() # redraw
            elif key == KEY_RETURN:
                theinput = self.input_text

                self.input_history.append(theinput)
                self.input_history_pos = len(self.input_history)

                self.input_text = ''
                self.input_pos = (1, 1)
                self.input_pane.addstr(self.input_pos[0], self.input_pos[1], ' ' * (curses.COLS - 2)) # visually erase input pane
                self.input_pane.refresh()

                return JanteMessage(theinput, sender=str(os.environ.get('USER')), recipient='#Local', address='#Local')
            elif key == KEY_UPARROW:
                if len(self.input_history) > 0 and self.input_history_pos > 0: # history not empty
                    if self.input_history_pos == len(self.input_history): # sitting at end
                        self.input_history_current = self.input_text

                    self.input_history_pos -= 1

                    self.input_text = self.input_history[self.input_history_pos]
                    self.input_pos = (1, 1 + len(self.input_text))

                    self.input_pane.addstr(self.input_origin[0], self.input_origin[1], ' ' * (curses.COLS - 2)) # visually erase input pane
                    self.input_pane.addstr(self.input_origin[0], self.input_origin[1], self.input_text)
            elif key == KEY_DOWNARROW:
                if self.input_history_pos < len(self.input_history):
                    self.input_history_pos += 1

                    if self.input_history_pos == len(self.input_history):
                        self.input_text = self.input_history_current
                    else:
                        self.input_text = self.input_history[self.input_history_pos]

                    self.input_pos = (1, 1 + len(self.input_text))

                    self.input_pane.addstr(self.input_origin[0], self.input_origin[1], ' ' * (curses.COLS - 2)) # visually erase input pane
                    self.input_pane.addstr(self.input_origin[0], self.input_origin[1], self.input_text)
            elif key == KEY_LEFTARROW:
                pass # TODO: moving around in input string, editing without erasing etc
            elif key == KEY_RIGHTARROW:
                pass # TODO: moving around in input string, editing without erasing etc
            else: # add to current input
                self.input_text += key
                self.input_pos = (self.input_pos[0], self.input_pos[1] + 1)

            return None
        except Exception as e:
            self.exit("Error recieving input.")
            traceback.print_exc()
            quit()
    def error(self, text):
        with self.output_buffer_mutex:
            for line in ('ERROR:' + str(text).strip()).split('\n'):
                self.output_buffer.append(line)
    def log(self, text):
        with self.output_buffer_mutex:
            for line in ('LOG:' + str(text).strip()).split('\n'):
                self.output_buffer.append(line)
