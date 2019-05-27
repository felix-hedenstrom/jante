#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading
import inspect
import copy

class EventHost:
    class callback:
        def __init__(self, target, prefilter, preprocessor):
            self.target = target
            self.prefilter = prefilter
            self.preprocessor = preprocessor

        def check_args_helper(self, obj, event_prototype):
            if obj == None:
                return

            args = inspect.getargspec(obj).args

            if 'self' in args:
                args.remove('self')

            if sorted(args) != sorted(inspect.getargspec(event_prototype).args):
                raise Exception("Event handler {} parameter mismatch: expected {}, got {}.".format(obj,
                    inspect.getargspec(event_prototype).args, args))

        # check for matching argument lists
        def check_args(self, event_prototype):
            self.check_args_helper(self.target, event_prototype)
            self.check_args_helper(self.prefilter, event_prototype)
            self.check_args_helper(self.preprocessor, event_prototype)

        def __eq__(self, other):
            return hash(self) == hash(other)

        def __hash__(self):
            return hash((self.target, self.prefilter, self.preprocessor))

    def __init__(self, logger=None):
        # per-event list of callbacks
        # _events[event_name] = [callback1, callback2, ...]
        self._events = dict()

        # mutex for the _events dict
        self._events_mutex = threading.Lock()

        # per-event function prototype for kwargs sanity checks
        # probably a dumb way to implement this
        self._event_prototypes = dict()

        # per-event list of callbacks for unavailable events (e.g not yet created)
        # when an event becomes available (e.g created), transfer all callbacks from
        #   waitingHandlers[] to events[]
        # when an event becomes unavailable (e.g destroyed), do the opposite
        self._waitingEventListeners = dict()

        self._logger = logger

        if self._logger == None:
            class mocklogger:
                def write(self, message):
                    pass

            self._logger = mocklogger()

    # add a callback as a waiting listener
    def _add_waiting_event_listener(self, event_name, target, prefilter=None, preprocessor=None):
        with self._events_mutex:
            # if the given event has no waiting list, create it
            if not event_name in self._waitingEventListeners:
                self._waitingEventListeners[event_name] = list()

            self._waitingEventListeners[event_name] += [EventHost.callback(target, prefilter,
                preprocessor)]

    # create an event
    def create_event(self, event_name, prototype):
        for arg in inspect.getargspec(prototype).args:
            if arg[0] == '_':
                raise Exception("Event keywords must not contain leading underscore: \"{}.{}\".".format(event_name, arg))

        with self._events_mutex:
            self._logger.write('Event created: {}'.format(event_name))
            self._events[event_name] = list()
            self._event_prototypes[event_name] = prototype

            # transfer any waiting handlers
            if event_name in self._waitingEventListeners:
                for cb in self._waitingEventListeners[event_name]:
                    self.add_event_listener(event_name, cb.target, cb.prefilter, cb.preprocessor)

                del self._waitingEventListeners[event_name]

    # destroy an event
    def destroy_event(self, event_name):
        with self._events_mutex:
            events_names = list(self._events[event_name])
            
        self._logger.write('Event destroyed: {}.'.format(event_name))

        # transfer any active listeners
        # TODO possible race conditions
        if event_name in self._events:
            for cb in event_names:
                self._add_waiting_event_listener(event_name, cb.target, cb.prefilter,
                        cb.preprocessor)
            
            with self._events_mutex:
                del self._events[event_name]
                del self._event_prototypes[event_name]

    # register a callback for an event
    def add_event_listener(self, event_name, target, prefilter=None, preprocessor=None):
        self._events_mutex.acquire()
        
        if not event_name in self._events:
            self._events_mutex.release()
            self._add_waiting_event_listener(event_name, target, prefilter, preprocessor)
        else:
            cb = EventHost.callback(target, prefilter, preprocessor)
            cb.check_args(self._event_prototypes[event_name])

            if __debug__:
                self._logger.write('New event listener: {} -> {}.'.format(event_name, target))


            self._events[event_name] += [cb]
            self._events_mutex.release()
    # unregister a callback for an event
    def remove_event_listener(self, event_name, target, prefilter=None, preprocessor=None):
        cb = EventHost.callback(target, prefilter, preprocessor)

        with self._events_mutex:
            if event_name in self._events and cb in self._events[event_name]:
                self._events[event_name].remove(cb)

    # fire an event
    def fire_event(self, _event_name, _eventLogEnabled=True, **kwargs):
        with self._events_mutex:
            if not _event_name in self._events:
                raise Exception("No such event \"{}\".".format(_event_name))

            # inspect parameters supplied to fire_event, comparing them to registered prototype
            protoargs = inspect.getargspec(self._event_prototypes[_event_name]).args
            missing = [val for val in protoargs if val not in kwargs.keys()]
            superfluous = [val for val in kwargs.keys() if val not in protoargs]

            if len(missing) > 0 or len(superfluous) > 0:
                message = list()

                if len(missing) > 0:
                    message.append("Missing keyword arguments: \"{}\".".format("\", \"".join(missing)))

                if len(superfluous) > 0:
                    message.append("Superfluous keyword arguments: \"{}\".".format("\", \"".join(superfluous)))

                raise Exception("fire_event({}) error: {}.".format(_event_name, ", ".join(message)))

            if _eventLogEnabled:
                self._logger.write('Firing event: {}.'.format(_event_name))

            newthreads = list()

            # run each callback in a new thread
            for cb in self._events[_event_name]:
                if cb.prefilter == None or cb.prefilter(**kwargs) == True:
                    args = copy.deepcopy(kwargs)

                    if cb.preprocessor != None:
                        args = cb.preprocessor(**args)

                    t = threading.Thread(target=cb.target, kwargs=args, name="{} - {}".format(_event_name, cb.target))
                    t.start()
                    newthreads.append(t)

            return newthreads
