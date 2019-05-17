#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import uuid
import random
import time
def smartpost(content, limit=5):
    """
    If the content has fewer rows than the specified limit the function returns 'content' without modifying it.
    If the content has equal or more rows an URL that leads to the content is returned.
    """
    assert type(limit) == int, "Limit must be an integer."
    assert type(content) == str, "Can only post strings."
    if len(content.split("\n")) < limit:
        return content
    return quickpost(content)

def quickpost(content):
    """
    Posts the content and returns either a link to the text or an error message in plaintext
    """
    finishedwithouterror, ans = post(content)
    return ans

def post(content):
    """
    Create a post on jantepaste

    :param str content: Text/data to post
    :return tuple (bool success, str result)

    Example::

        import JantePasteDB
        status, result = JantePasteDB.post("Hello, World!")

    """
    raise NotImplementedError()
    # TODO: get this value from the bot/settings somehow
    base_url = 'example.com:port/paste/{key}'

    try:
        key = JantePasteDB().post(str(content))
        return (True, base_url.format(key=key))
    except Exception as e:
        return (False, "JantePasteDB.post(): Error - " + str(e))


class JantePasteDB:
    # singleton-esque storage
    _database = dict()
    _ttl = dict() # _ttl[key] = unixtime deadline in seconds for
                  # deleting _database[key] (and _ttl[key])
    _last = None
    # keygen = a function that generates "random" keys (names) for pastes
    def __init__(self, keygen=None):
        if keygen == None:
            keygen = JantePasteDB.readable_keygen

        self._keygen = keygen

    @staticmethod
    def uuid4_keygen(data):
        return str(uuid.uuid4())

    # this keygen generates random sequences of vowel-consonant pairs, similar
    # to hastebin, e.g "uveconokiv", "ycejalycyr"
    @staticmethod
    def readable_keygen(data):
        vowels = ['a', 'e', 'i', 'o', 'u']
        consonants = ['b', 'c', 'd', 'f', 'g', 'h', 'k', 'l', 'm',
                      'n', 'p', 'r', 's', 't', 'v', 'x', 'z']

        length = 5

        # create list of random ints
        result = list(map(lambda x: random.randint(0, 2**64), range(length)))

        # randomization of starting with vowel or consonant
        c = random.randint(0,1)

        # replace each random int in list with vowel or consonant
        for i in range(length):
            if (i+c) % 2 == 1:
                result[i] = vowels[result[i] % len(vowels)]
            else:
                result[i] = consonants[result[i] % len(consonants)]

        return ''.join(result)

    # remove dead entries on ttl expiration
    def _purge(self):
        now = time.time()

        for key in list(JantePasteDB._database.keys()):
            if JantePasteDB._ttl[key] <= now:
                del JantePasteDB._database[key]
                del JantePasteDB._ttl[key]

    # post() returns key for stored entry such that get(post('foo')) = 'foo'
    # throws exception if N rounds of the keygen didnt produce a unique key
    def post(self, data, ttl=86400/2): # default ttl is 24 hours (24*60*60 seconds)
        self._purge()

        # try to find a nonexistant key
        key = self._keygen(data)
        tries = 0

        while key in JantePasteDB._database:
            key = self._keygen(data)
            tries += 1

            if tries > 1000:
                raise Exception('keygen seems unable to produce a unique key')

        # store the entry
        JantePasteDB._database[key] = data
        JantePasteDB._ttl[key] = time.time() + ttl

        JantePasteDB._last = data

        return key

    def get_last(self):
        return self._last

    def contains(self, key):
        self._purge()

        return key in JantePasteDB._database

    # throws KeyError exception
    def get(self, key):
        self._purge()

        return JantePasteDB._database[key]
