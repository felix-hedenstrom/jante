import threading

import copy

import math

import jsonpickle

from plugins.jantecoin.currency.jantecoin import JanteCoin #JanteCoinFactory, JanteCoin

class MoneyManager:
    def __init__(self, filename, bank_name, precision, bank_start_money, drop_off_factor):
        self._mutex = threading.Lock()
        self._filename = filename
        self._bank_name = bank_name
        self._precision = precision
        self._drop_off_factor = drop_off_factor
        try:
            with open(self._filename, "r") as f:
                self.__ledger = jsonpickle.decode(f.read())

        except:
            self.__ledger = dict()
            self.__ledger[bank_name] = JanteCoin(bank_start_money, parts_in_whole=self._precision)
    def save(self):
        with open(self._filename, "w") as f, self._mutex:
            f.write(jsonpickle.encode(self.__ledger))

    @property
    def bank_name(self):
        with self._mutex:
            return self._bank_name
    @property
    def ledger(self):
        with self._mutex:
            return copy.deepcopy(self.__ledger)

    def has_account(self, person):
        with self._mutex:
            return person in self.__ledger

    def create_account(self, person):
        with self._mutex:

            if person in self.__ledger:
                raise ValueError("Person already has an account.")
            self.__ledger[person] = JanteCoin(0, 0, self._precision)

    def str_to_coin(self, _str):
        return self.float_to_coin(float(_str))  #JanteCoinFactory(_str, parts_in_whole=self._precision)

    def float_to_coin(self, _float):
        return _float * JanteCoin(1, 0, self._precision)

    def get_amount(self, person):
        with self._mutex:
            return self.__ledger[person]

    def get_multiplier(self, person):
        with self._mutex:
            return 2 / pow(2, math.log(self.__ledger[person].to_float() + self._drop_off_factor, self._drop_off_factor))

    def transfer(self, amount, _from, to):
        if not type(amount) == JanteCoin:
            raise RuntimeError("Must be a JanteCoin type")

        if amount < 0:
            raise RuntimeError("Number can't be smaller than 0.")

        with self._mutex:
            if not _from in self.__ledger:
                raise RuntimeError("Person {} does not have an entry in the ledger.".format(_from))

            if not to in self.__ledger:
                raise RuntimeError("Person {} does not have an entry in the ledger.".format(to))

            if self.__ledger[_from] < amount:
                raise RuntimeError("Can't send more money than you have.")

        with self._mutex:
            self.__ledger[_from] = self.__ledger[_from] - amount
            self.__ledger[to] = self.__ledger[to] + amount
