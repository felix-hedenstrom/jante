#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
@author Felix Hedenström
Controls the jantebot.
Uses a specified type of IO (eg XMPP, IRC, Local machine)
to process chatcommands. It then sends the chatcommand to any
plugin matching the prefix specified in the command.
'''

import sys

import argparse

import copy
import time 
import re
import traceback
import threading

import inspect
#import os
# Parses settings.ini
import configparser

import queue

# All user made plugins
import plugins

# Helpful jantespecific libraries
from libs.jantehttpd import JanteHTTPD
from libs.jantemessage import JanteMessage
from libs.eventhost import EventHost
from libs.jantetable import get_table 
from libs.janteio.iomanager import IOManager
from libs.servicemanager.servicemanager import ServiceManager

class Bot:
        
    def offer_service(self, name, service):
        """
        Used by plugins to offer services like dictionaries. Name is the name of the service and
        "service" is a object of type libs/servicemanager/service
        """
        return self._service_manager.offer_service(name, service)
    def get_service(self, name):
        """
        Returns a service object if it exists.
        """
        return self._service_manager.get_service(name)

    # setup connection as defined per settings
    def __init__(self, iotype, settingsfile, testing=False):
        self._shutdown_called = False
        self._muted = False
        self._mutex = threading.Lock()
        self._threads = []
        self._threadlimit = 20
        self._message_queue = queue.Queue()
        self._commands = dict()
        self._config = settingsfile 
        

        plugins.import_all(self._config)

        self._io = IOManager(iotype, self)
        
        self._httpd = None
        self._httpd_routes = dict()
        # Initiate service servicemanager
        self._service_manager = ServiceManager()

        # initialize events subsystem
        class IOLoggerAdapter:
            def __init__(self, io):
                self.io = io

            def write(self, message):
                self.io.log(message)

        self._events = EventHost(IOLoggerAdapter(self._io))
        # function call prototype (keyword spec) for stock events
        def on_message(message): pass
        def on_message_sent(message): pass
        def on_plugins_loaded(): pass
        def should_save(): pass
        def on_timer_tick(timeval): pass

        self._events.create_event("on_message", on_message)
        self._events.create_event("on_message_sent", on_message_sent)
        self._events.create_event("on_plugins_loaded", on_plugins_loaded)
        self._events.create_event("should_save", should_save)
        self._events.create_event("on_timer_tick", on_timer_tick)

        def show_commands(message):
            self.add_message(message.respond("{}.".format(', '.join(list(sorted(self._commands)))), self.get_nick()))
        def reload_IO(message):
            self.add_message(jantemessage("Started reloading, this might take a while.", address=message.get_address(), sender=self.get_nick(), is_in_group=message.isInGroup()))
            self.add_message(jantemessage(self._reload(), address = message.get_address(), isInGroup = message.isInGroup(), recipient=message.get_sender(), sender=self.get_nick()))
        # Client requests a list of plugins
        def plugins_IO(message):
            with self._mutex:
                self._plugins = sorted(self._plugins, key=lambda p: inspect.getfile(p.__class__).split("/")[-2])
                ans = jantetable.getTable([list(map(lambda p: inspect.getfile(p.__class__).split("/")[-2], self._plugins)), list(map(lambda p: p.getDescription(), self._plugins))], ["Plugin", "Description"])
            self.add_message(jantemessage(ans, address = message.get_address(), isInGroup = message.isInGroup(), recipient = message.get_sender(), sender=self.get_nick()))
        def save_command(message):
            """
            Tells all plugins that are listening to the "should_save" event to save.
            """
            self.add_message(message.respond("Telling all plugins to save...", self.get_nick()))
            self.fire_event("should_save")

        self.add_command_listener('commands', show_commands)
        self.add_command_listener('reload', reload_IO)
        self.add_command_listener('plugins', plugins_IO)
        self.add_command_listener('save', save_command)


        self._loadplugins()



        def timerThread():
            while not self._shutdown_called:
                time.sleep(1.0)
                t = time.time()
                self.fire_event('on_timer_tick', _eventLogEnabled=False, timeval=t)

        t = threading.Thread(target=timerThread, name="TimerThreadMain - Sends on_timer_tick events")
        t.start()
        
        with self._mutex:
            self._threads.append(t)

    def register_command(self, owner, command, description="No description"):
        with self._mutex:
            if not command in self._commands:
                self._commands[command] = {'owner':owner, 'description':description}
                return True
            else:
                return False

    def unregister_command(self, owner, command):
        with self._mutex:
            if command in self._commands and self._commands[command]['owner'] == owner:
                del self._commands[command]
                return True
            else:
                return False

    def get_config(self, section=None):
        if section == None:
            return copy.copy(self._config)
        else:
            try:
                return copy.copy(self._config[section])
            except KeyError:
                return dict()

    def get_nick(self):
        return self._config['global']['nick']

    def get_command_prefix(self):
        return self._config['global']['prefix']
    def get_base_data_path(self):
        return '{datadir}'.format(datadir=self._config['global']['datapath'])
    def paste(self, text, message=None):
        return self.get_service("paste").paste(text, message)
    def get_data_path(self, plugname, filename):
        if plugname == 'anagram': # TODO: get rid of this special case
            return '{datadir}/{plugdir}/{filename}'.format(
                datadir=self._config['global']['datapath'], plugdir=plugname, filename=filename)
        else:
            return '{datadir}/{filename}'.format(
                datadir=self._config['global']['datapath'], filename=filename)

    def create_event(self, event_name, prototype):
        self._events.create_event(event_name, prototype)

    def destroy_event(self, event_name):
        self._events.destroy_event(event_name)

    def add_event_listener(self, event_name, target, prefilter=None, preprocessor=None):
        self._events.add_event_listener(event_name, target, prefilter, preprocessor)

    def remove_event_listener(self, event_name, target, prefilter=None, preprocessor=None):
        self._events.remove_event_listener(event_name, target, prefilter, preprocessor)

    def fire_event(self, event_name, **kwargs):
        self._threads += self._events.fire_event(event_name, **kwargs)
    
    def number_of_threads(self):
        self._pruneThreads()
        with self._mutex:
            n = len(self._threads)
        return n

    def get_commands(self):
        return copy.copy(self._commands)

    def add_command_listener(self, command, callback, strip_preamble=False, direct_reply=False):
        """
        Convenience method for creating an event listener that listens to basic chat commands.

        Args:
        command (str): The textual part of the command (i.e without any command prefix symbol)
        callback (callable): Target function to call upon the bot seeing the command.

        Keyword args:
        strip_preamble (bool): Whether or not to strip the command prefix symbol and command text
                               from the message text before sending it to the target function.
                               example: If False, callback will see "!command foo bar". If True,
                               callback will see "foo bar".
        direct_reply (bool):   Whether or not to assume the target function to return a single
                               string intended to be sent as a chat message. If True, the given
                               target function will be wrapped in a closure that will receive said
                               string and automatically perform the actual sending of the message.
        """
        target = callback

        self.register_command('bot.add_command_listener', command)

        def command_listener_filter(message):
            if re.match(r'{prefix}{command}($|\s)'.format(
                prefix = re.escape(self._config.get('global', 'prefix')),
                command = re.escape(command)), message.get_text()):
                return True
            else:
                return False

        if direct_reply:
            def command_listener_wrapper(message):
                try:
                    reply = str(callback(message))
                    if reply.strip() == "":
                        self.add_message(message.respond("Something went wrong. Plugin sent an empty message.", self.get_nick()))
                    if not type(reply) == str:
                        self.add_message(message.respond('Something went wrong. Expected string but plugin sent "{}".'.format(type(reply)), self.get_nick()))
                    self.add_message(message.respond(reply, self.get_nick()))
                except:
                    errormsg = traceback.format_exc()
                    self.error('BOT::{}'.format(errormsg))
                    self.add_message(message.respond('Error in event handler {}.'.format(str(callback)), self.get_nick()))

            target = command_listener_wrapper

        if strip_preamble:
            def command_listener_processor(message):
                regex = r'^{prefix}{command}($|\s)'.format(
                    prefix = re.escape(self._config.get('global', 'prefix')),
                    command = re.escape(command))

                mymessage = message.clone()
                mymessage.set_text(re.sub(regex, '', message.get_text()))

                return {'message': mymessage}

            self._events.add_event_listener('on_message', target, prefilter=command_listener_filter,
                preprocessor=command_listener_processor)
        else:
            self._events.add_event_listener('on_message', target, prefilter=command_listener_filter)
    def configure_alias(self, message):
        """
        Sets alias if configured to do so,
        does nothing if alias not configured to be used.
        """
        if not self._config.getboolean('global', 'use_aliases', fallback=False):
            message.set_alias(message.get_sender())
            return message
        else:
            # Add alias to message
            alias = self._service_manager.get_service("alias").get_alias(message.get_sender()) 
            message.set_alias(alias)
            return message
    
    def add_message(self, message):
        message = self.configure_alias(message)
        self.log('enqueued a message: {}'.format(message.get_text()))

        self._message_queue.put(message)

    def _waitForThreads(self, threadsthatshouldlive=2):
        """
        Waits for all but <threadsthatshouldlive> threads to die.
        """

        self._pruneThreads()

        with self._mutex:
            threadcount = len(self._threads) - threadsthatshouldlive

        if threadcount > 0:
            self.log("Waiting for threads to die.")
            self.log("Currently {} threads active.".format(threadcount))

            while(threadcount > 0):
                oldthreadcount = threadcount
                self._pruneThreads()
                with self._mutex:
                    threadcount = len(self._threads) - threadsthatshouldlive
                if not oldthreadcount == threadcount:
                    self.log("Waiting for {} remaining threads...".format(threadcount))

        self.log("All threads have stopped. This is intentional. Continuing...")

    def _reload(self):
        """
        Reloads all plugins if their code has been altered during runtime.
        Waits for all but the necessary threads to be shut down.
        Fires the "should_save" event and waits for the threads to finish saving before
        reloading them.

        TODO: Not currently working. Does nothing and takes a while to do it.
        """


        self.fire_event("should_save")

        return "Not implemented at this time."

        try:

            #imp.reload(plugins)
            #reimport.reimport(plugins)
            #xreload.xreload(plugins)
            self._loadplugins()

            return "Reloaded all modules."
        except:
            errormsg = traceback.format_exc()
            self.error(errormsg)
            return "Could not reload all modules, check stacktrace."

    def __loadSubClasses(self, obj):
        bad_plugins = []
        for o in obj.__subclasses__():
            if o is not plugins.plugintemplate.PluginTemplate and isinstance(o,type):
                if not self.__loadplugin(o):
                    bad_plugins.append(o.__name__)
                bad_plugins += self.__loadSubClasses(o)
        return bad_plugins

    # Loads singular plugin
    def __loadplugin(self, plugin):
        """
        Returns True if plugin was loaded, False otherwise
        """
        # Classes that are templates and should not be regarded as plugins
        if plugin == plugins.parsingplugintemplate.ParsingPluginTemplate:
            return True

        if __debug__:
            self.log('Initializing plugin class "{}".'.format(plugin.__name__))
        try:
            p = plugin(self)
        except:
            errormsg = traceback.format_exc()
            self.error(errormsg)
            self.error('Fatal error occured initializing plugin "{}". Check stacktrace.'.format(plugin.__name__))
            return False

        with self._mutex:
            self._plugins.append(p)
        if __debug__:
            self.log('Loaded "{}".'.format(plugin.__name__))
        return True
   
    #Add new plugins to this list and to the 'reload' command
    #inside respond
    def _loadplugins(self):
        self.log("Loading plugins.")

        with self._mutex:
            self._plugins = []

        self._waitForThreads()
        bad_plugins = self.__loadSubClasses(plugins.plugintemplate.PluginTemplate)
        if len(bad_plugins):
            self.error(
            """
               !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
               FATAL ERROR(S) HAVE OCCURRED WHEN LOADING PLUGINS!
               !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
               Could not load {} plugin(s). Please report the errors printed in the log.
               Plugins that could not be loaded: {}.""".format(len(bad_plugins), ", ".join(bad_plugins)))
        self.log("Done loading plugins.")

    # Removes threads that are not active
    def _pruneThreads(self):
        with self._mutex:
            self._threads = [t for t in self._threads if t.is_alive()]

        return

    # Starts the bot so that it starts reading the chat
    def start(self):
        if self._config.getboolean('webjante','enabled'):
            self.log("Starting Webjante.")
            self.start_httpd(  int(self._config['webjante']['port']), self._config['webjante']['passw'],
                            self._config['webjante']['sslkeyfile'], self._config['webjante']['sslcertfile'])
        else:
            self.log("Webjante not configured to start.")
        self.log("Starting mainbot!")
        # start the sending thread
        def send_messages():
            while not self._shutdown_called:
                if not self._muted and not self._message_queue.empty():
                    message_to_send = self._message_queue.get()
                    if message_to_send.get_address() == None or message_to_send.get_address() == "":
                        self.error("ATTEMPTED TO SEND MESSAGE WITHOUT ADDRESS.")
                        time.sleep(0.05)
                    elif type(message_to_send.get_address()) == tuple:
                        
                        # Internal message.
                        self.log('Internal message sent with id "{}"'.format(message_to_send.get_address()))
                        self.fire_event('on_message_sent', message=message_to_send)
                    else:
                        self.log('Sending message to address "{}"'.format(message_to_send.get_address()))

                        if issubclass(type(message_to_send.get_text()), BaseException):
                        # Errors should be formatted correctly before they are sent to external sources
                            message_to_send.set_text("{}-exception::{}: {}".format(message_to_send.get_sender(), type(message_to_send.get_text()).__name__, message_to_send.get_text().args[0]))

                        self._io.send(message_to_send)
                        self.fire_event('on_message_sent', message=message_to_send)
                        time.sleep(0.05)
                else:
                    time.sleep(0.1)
        
        t = threading.Thread(target=send_messages, name="send_messages_main - Triggers on_message_sent")
        
        t.start()
        
        self._threads.append(t)
        while not self._shutdown_called:
            message = self._io.recieve()

            if message == None:
                continue

            # TODO: replace this with some proper method of the
            # TODO: .. IO signalling back to the bot that the IO
            # TODO: .. is closing down
            if message.get_text() == message.get_address() == message.get_sender() == 'QUIT':
                self._shutdown()
                return

            # Add alias to message
            message = self.configure_alias(message)
            # Prints all read lines into stdout
            if message.get_text().strip() != "":

                ans = ""

                if not message.is_in_group():
                    ans += "\tPrivate message:\n"
                else:
                    ans += "\tGroup message:\n"
                ans += "\t\tText:\n{}\n\t\tFrom:{}\n\t\tAddress:{}\n".format(message.get_text(), message.get_alias(), message.get_address())
                self.log(ans)

            # If a client has sent <prefix>pull and the settins allow for it, kill Jante
            if self._config.getboolean('global', 'allow_git_pull', fallback=False) and message.get_text().strip().startswith("{}pull".format(self._config['global']['prefix'])):
                self._io.exit("Pulling from git and restarting")
                sys.stderr.write("Exited in order to perform git pull.\n")
                self._shutdown()

            # If a normal message is gotten, fire on_message.
            if not message.get_sender() == "" and not message.get_text() == "" and len(message.get_sender().split(" ")) == 1:
                self.fire_event('on_message', message=message)

            # If there are too many threads running, kill them
            if len(self._threads) > self._threadlimit:
                self.log("Pruning threads.")
                self._pruneThreads()

            if len(self._threads) > self._threadlimit:
                self._io.exit("Too many threads, shutting down")
                self._shutdown()


        self._waitForThreads()
        raise SystemExit()

    def start_httpd(self, port, password, keyfile='ssl/key.pem', certfile='ssl/cert.pem'):
        def webresponder(req):
            self.log('httpd: <<< [{}] GET {}'.format(req.client_address[0], req.path))

            for p in self._httpd_routes.keys():
                if re.match(re.escape(p), req.path): # TODO: pick longest match
                    self.log('httpd: >>> {} -> {}'.format(req.path, self._httpd_routes[p]))
                    self._httpd_routes[p](req)
                    return

            if req.path == '/':
                self.log('httpd: >>> 200 Hello from jante')
                req.send_http_response_code(200)
                req.send_http_header('Content-type', 'text/plain')
                req.send_http_output('Hello from jante')
            else:
                self.log('httpd: >>> 404 Not found')
                req.send_http_response_code(404)
                req.send_http_header('Content-type', 'text/plain')
                req.send_http_output('Not found')

        self.log("Starting httpd.")

        assert self._httpd == None

        self._httpd = jantehttpd.jantehttpd(port, password, webresponder, self._io, keyfile, certfile)
        self._httpd.start_in_thread()

    def register_web_route(self, route, target):
        if __debug__:
            self.log("Registering httpd route {} -> {}".format(route, target))
        self._httpd_routes[route] = target

    def unregister_web_route(self, route):
        if __debug__:
            self.log("Unregistering httpd route {}".format(route))
        del self._httpd_routes[route]
    
    def clear_web_routes(self):
        self.log("Clearing httpd routes")
        self._httpd_routes = dict()
    def shutdown(self):
        self._shutdown()
    def _shutdown(self):
        self.fire_event("should_save")
        self._shutdown_called = True

        if self._httpd != None:
            self._httpd.shutdown()
            self._httpd = None

    def error(self, text):
        self._io.error(text)

    def log(self, text):
        self._io.log(text)

def main(argv):
    parser = argparse.ArgumentParser(description='The jante-bot. Created to easily integrate various plugins. The bot has a number possible IO types. By default it uses the local IO that is called by -l', prog='jante-bot')

    g = parser.add_mutually_exclusive_group()

    # Normal Protocols
    g.add_argument('-x', '--xmpp', action='store_const', const="xmpp", dest="io", help="Use the XMPP protocol.")
    g.add_argument('-i', '--irc', action='store_const', const="irc", dest="io", help="Use the IRC protocol.")
    g.add_argument('-d', '--discord', action='store_const', const="discord", dest="io", help="Use Discord.")

    # Local IO
    g.add_argument('-b', '--barebones', action='store_const', const="old", dest="io", help="Use a barebones local IO system. Mainly for testing things on a local machine. Less functional than --local.")
    g.add_argument('-o', '--old', action='store_const', const="old", dest="io", help="Deprecated name for -b.")
    g.add_argument('-l', '--local', action='store_const', const="local", dest="io", help="Use a curses based local IO system. Mainly for testing things on a local machine.")


    # Parse arguments
    args = parser.parse_args(argv)
    
    config = configparser.ConfigParser()
    config.read('bot-settings.ini')
    # Run the bot as you would normally
    b = Bot(args.io, config,testing=False)
    b.start()

if __name__ == "__main__":
    main(sys.argv[1:])
