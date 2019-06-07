from plugins.eval.syntaxhandlers.lexer import lexer
from plugins.eval.syntaxhandlers.parser import parser
from plugins.eval.syntaxhandlers.jantetoken import action
from libs.jantemessage import JanteMessage

import threading
import traceback

import time
from datetime import datetime, timedelta

import copy

class Evaluator:
    def __init__(self, message, id_, bot, timelimit, prefix):
        self._original_message = message
        self._bot = bot
        self._lexer = lexer()
        self._parser = parser()
        self._steps = 0
        self._messages = []
        self._mutex = threading.Lock()
        self._id = id_ 
        self._timelimit = timelimit

        self._prefix = prefix

        def message_filter(message):
            return message.get_address() == self._id
        self._filter = message_filter
        self._bot.add_event_listener('on_message_sent', self.listener, prefilter=self._filter)

    def remove_listener(self):
        self._bot.remove_event_listener('on_message_sent', self.listener, prefilter=self._filter)

    def listener(self, message):
        with self._mutex:
            self._messages.append(message)

    def evaluate(self, text):
        try:
            tokens = self._lexer.lex(text)
        except ValueError as e:
            return e 
        try:
            tree = self._parser.parse(tokens)
        except ValueError as e:
            return e
        var_dict = dict()
        return self.__run_tree(tree, var_dict)

    def has_incoming_message(self):
        with self._mutex:
            return len(self._messages)

    def __process(self, command):

        m = JanteMessage(command, sender=self._original_message.get_sender(), address=self._id)
        m.set_alias(self._original_message.get_alias())
        self._bot.fire_event('on_message', message=m)

        while(not self.has_incoming_message() and datetime.now() < self._timelimit):
            time.sleep(0.02)

        if not datetime.now() < self._timelimit:
            return RuntimeError("Ran out of time on command {}.".format(command))

        with self._mutex:
            inc_message = self._messages.pop()
            self._messages = []

        return inc_message.get_text()

    def __error(self, command, answer):
        return RuntimeError("\"{}\" evaluated to a {}. Error description: {}".format(self._bot.getService("paste").paste(command), answer.__class__.__name__, answer.args[0] ))



    def __run_tree(self, tree, variables):
        command = ""
        for branch in tree:

            if type(branch) == str:
                command += branch

            elif type(branch) == action.suppress:
                answer = self.__process(command)
                if issubclass(type(answer), BaseException):
                    return self.__error(command, answer)
                elif not type(answer) == str:
                    raise RuntimeError("\"{}\" did not evaluate to a string but a {}. This should never happen.".format(command,type(answer)))
                command = ""

            elif type(branch) == action.variable_assign:
                partans = self.__run_tree(branch.getValue(), copy.deepcopy(variables))
                if issubclass(type(partans), BaseException):
                    return self.__error(command, partans)
                variables[branch.getIdentifier()] = partans

            elif type(branch) == action.variable_deref:
                if not branch.getIdentifier() in variables:
                    raise ValueError("Cannot dereference variable {} before it is assigned.".format(branch.getIdentifier()))
                command += variables[branch.getIdentifier()]

            else:
                # Must be tree of things that must be evaluated.
                assert type(branch) == list
                partans = self.__run_tree(branch, copy.deepcopy(variables))
                if not type(partans) == str:
                    return partans
                command += partans

        if not command.strip().startswith(self._prefix):
            return command

        answer = self.__process(command.strip())
        if not type(answer) == str:
            return self.__error(command, answer)
        return answer
