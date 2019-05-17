#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Author Felix Hedenström
Used to send messages within Jante. Contains information about who sent the message and where it is going.

Remade to be PEP8 compliant on 2019-05-17
"""
import copy

class JanteMessage():
    """
    A message. Sent through IRC, XMPP or even the local tested enviroment
    locally, messages contain the information sent in the messages
    as well as who the sender was and what channel it was sent on.

        text            - Text that the message contains
        sender          - Sender of the message
        recipient       - recipient of the message
        address         - Address of the sender. Internal messages are sent with a tuple instead of a string.
        is_in_group     - Is the message from a groupchat?
        send_to_all     - Should the message be sent to all channels?
    """
    def __init__(self, text="", sender="", recipient="", address="", is_in_group=True, send_to_all=False):

        assert type(text) == str or issubclass(type(text), BaseException) , "'text' must be of type string or exception."
        assert type(sender) == str, "'sender' must be of type string."
        assert type(recipient) == str, "'recipient' must be of type string."
        assert type(is_in_group) == bool, "'is_in_group' must be of type bool"
        assert type(send_to_all) == bool, "'send_to_all' must be of type bool"

        self._text = text
        self._sender = sender
        self._recipient = recipient
        self._address = address
        self._is_in_group = is_in_group
        self._send_to_all = send_to_all
        self._alias = None
    
    def is_internal(self):
        """
        Internal messages are sent with tuples instead of the normal channel or direct message path
        """
        return type(self._address) == tuple
    
    def set_text(self, text):
        assert type(text) == str, "'text' must be of type string"
        self._text = text
        return self
        
    def set_alias(self, alias):
        self._alias = alias
        return self
        
    def get_alias(self):
        return self._alias 
        
    def set_recipient(self,recipient):
        assert type(recipient) == str, "'recipient' must be of type string."
        self._recipient = recipient
        return self
    def set_sender(self, sender):
        assert type(sender) == str, "'user' must be of type string"
        self._sender = sender
        return self
        
    def set_address(self, address):
        self._address = address
        return self
        
    def set_is_in_group(self, is_in_group):
        assert type(is_in_group) == bool, "'is_in_group' must be of type bool"
        self._is_in_group = is_in_group
        return self
        
    def set_send_to_all(self, send_to_all):
        assert type(send_to_all) == bool, "'sendToAll' must be of type bool"
        self._send_to_all = send_to_all
        return self
        
    def respond(self, text, sender):
        m = JanteMessage(text, sender, self._sender, self._address, self._is_in_group, self._send_to_all)
        return m

    def clone(self):
        return copy.copy(self)

    def get_text(self):
        return self._text

    def get_sender(self):
        return self._sender
    def get_recipient(self):
        return self._recipient

    def is_in_group(self):
        return self._is_in_group
    def should_send_to_all(self):
        return self.get_send_to_all()

    def get_send_to_all(self):
        return self._send_to_all
    
    def get_address(self):
        return self._address

    def to_string(self):
        ans = "Sender: {}\n".format(self._sender)
        ans += "Text:\n\t{}".format(self._text)
        return ans
    
    def __repr__(self):
        return 'jantemessage{}'.format(str(self.__dict__))
