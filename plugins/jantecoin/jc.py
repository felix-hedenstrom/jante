
import shlex
import argparse
import re

import configparser

import pickle
import threading

import copy

import json

import random

from plugins.parsingplugintemplate import ParsingPluginTemplate

from plugins.jantecoin.managers.drop import CoinDrop
from plugins.jantecoin.managers.money_manager import MoneyManager


class JantecoinPlugin(ParsingPluginTemplate):

    def __init__(self, bot):
        self._config = configparser.ConfigParser()

        self._config.read("plugins/jantecoin/settings.ini")

        super().__init__(bot, command=self._config["plugin"]["command"], description="Jantes own currency!")

        self._mutex = threading.Lock()

        self._filename_channels = "{}{}.json".format(self._bot.get_base_data_path(), self._config['plugin']["channels_file_name"])


        try:
            with open(self._filename_channels, "r") as f:
                self._channels = json.load(f)
        except:
            self._channels = list()

        self._coin_drop_manager = CoinDrop(self._config, self)
        # Event listeners
        self._bot.add_event_listener('should_save', self.save)
        self._bot.add_event_listener("on_message", self.passive_gain)

        self._bot.add_event_listener("on_timer_tick", self._coin_drop_manager.maybe_drop_currency)

        self._full_name = self._config["currency"]["full_name"]
        self._save_limit = self._config.getint("plugin", "save_after_n_messages")
        self._precision = self._config.getint("currency", "data_precision")

        self.__count = 0
        self._money_manager = MoneyManager("{}{}.jsonpickle".format(self._bot.get_base_data_path(),
                                           self._config['plugin']['ledger_file_name']),
                                           self._config["currency"]["bank_name"],
                                           self._precision,
                                           self._config.getint('currency',"total_coins"),
                                           self._config.getint('variables', "drop_off_factor")
                                           )

        self.parser = argparse.ArgumentParser(description=self._description, prog=self._config["currency"]["shorthand"], add_help=False)
        self.parser.add_argument('--grab', action='store_true', help="Grab any recently dropped {}.".format(self._full_name))
        self.parser.add_argument('--raffle', action='store_true', help="Enter the raffle to win {}.".format(self._full_name))
        self.parser.add_argument('--amount', nargs="?", metavar="PERSON", const=True, help="See the amount of {} you have.".format(self._full_name))
        self.parser.add_argument('--send', nargs=2, metavar=("AMOUNT", "PERSON"), help="Send {} to this person.".format(self._full_name))
        self.parser.add_argument('-h', '--help', action='store_true', required=False, help="Shows this helpful message.")
        self.parser.add_argument("--raw", action="store_true", help="Returns the data in a more raw form. Removes all but the essential data.")
        self.parser.add_argument("--multiplier", nargs="?", metavar="PERSON", const=True, help="See your {} earnings multiplier.".format(self._full_name))
        self.parser.add_argument("--ledger", action="store_true", help="See how much everyone has.")
        self.parser.add_argument("--join", action="store_true", help="Let this channel join in on currency drops.")
        self.parser.add_argument("--leave", metavar="CHANNEL", help="Make this channel no longer have currency drops.")
        self.parser.add_argument("--channels", action="store_true", help="List all channels where currency can drop.")
        self.parser.add_argument("--gamble", type=self._money_manager.str_to_coin, help=r"Gamble the amount entered for a 49 percent chance to double your money.")

    def get_channels(self):
        with self._mutex:
            return copy.deepcopy(self._channels)
    def save(self):
        self._money_manager.save()

        with open(self._filename_channels, "w+") as f, self._mutex:
            json.dump(self._channels, f)

    def passive_gain(self, message):
        """
        Passive gain of currency.
        """
        # If internal message, no currency will be gained.
        if type(message.get_address()) == tuple or not message.is_in_group():
            return

        person = message.get_alias()

        if not self._money_manager.has_account(person):
            self._money_manager.create_account(person)

        money = self._money_manager.float_to_coin(self._money_manager.get_multiplier(person) * self._config.getfloat("variables", "passive_rate"))


        self._money_manager.transfer(money, self._money_manager.bank_name, person)

        self.__count += 1
        if self.__count > self._save_limit:
            self.save()
            self.__count = 0

    def parse(self, message):
        try:
            args = self.parser.parse_args(shlex.split(message.get_text()))

        except BaseException as e:

            return RuntimeError("Could not parse message. {}".format(self.parser.format_usage()))

        if not self._money_manager.has_account(message.get_alias()):
            self._money_manager.create_account(message.get_alias())

        if args.help:
            return self.parser.format_help()

        if args.join:
            with self._mutex:
                if not message.is_in_group():
                    return RuntimeError("Can only have {}-events in group chats.".format(self._full_name))
                elif message.get_address() in self._channels:
                    return RuntimeError("That channel already has the possiblility to drop {}".format(self._full_name))
                elif type(message.get_address()) == tuple:
                    return RuntimeError("This is an interal message. Can't drop currency in internal channels.")
                else:
                    self._channels.append(message.get_address())
                    return "Added channel!"

        if args.gamble:
            person = message.get_alias()
            if args.gamble < 0:
                return ValueError("Can't gamble for negative money.")

            if self._money_manager.get_amount(self._money_manager.bank_name) < args.gamble:
                return ValueError("Can't gamble for more than the bank owns.")

            if self._money_manager.get_amount(person) < args.gamble:
                return ValueError("Can't gamble more money than you own. You only have {}{}.".format(self._money_manager.get_amount(person), self._config["currency"]["shorthand"]))

            if random.random() > 0.51:
                response = self._money_manager.transfer(args.gamble, self._money_manager.bank_name, person)
                won = True
            else:
                response= self._money_manager.transfer(args.gamble, person, self._money_manager.bank_name)
                won = False

            if issubclass(type(response), Exception):
                return response

            self.save()

            if won:
                return "You won {amount}{curr}!!! You now have {total}{curr}.".format(amount=args.gamble, curr=self._config["currency"]["shorthand"], total=self._money_manager.get_amount(person))
            else:
                return "You lost {amount}{curr}... You now have {total}{curr}.".format(amount=args.gamble, curr=self._config["currency"]["shorthand"], total=self._money_manager.get_amount(person))

        if args.leave:
            with self._mutex:
                try:
                    self._channels.remove(args.leave)
                except:
                    return RuntimeError("Can not remove an element that does not exist in the list.")
                return "Removed channel {}.".format(args.leave)

        if args.channels:
            with self._mutex:
                if len(self._channels) == 0:
                    return "There are no channels where you can get {}.".format(self._full_name)
                ans = ""
                for name in self._channels:
                    ans += "{}\n".format(name)
                return ans

        if args.grab:
            person = message.get_alias()

            if self._coin_drop_manager.grab():
                reward = self._money_manager.float_to_coin(self._money_manager.get_multiplier(message.get_alias()) * self._coin_drop_manager.award())
                self._money_manager.transfer(reward, self._money_manager._bank_name, person)

                self.save()
                return "{per} just won {aw}{curr}.".format(per=person, aw=str(reward), curr=self._config["currency"]["shorthand"])
            else:
                return "The event is not active now."


        if args.raffle:
            return NotImplementedError("This function is not implemented yet.")

        if args.multiplier:
            if not type(args.multiplier) == str:
                person = message.get_alias()
            else:
                person = args.multiplier

            if not self._money_manager.has_account(person):
                return KeyError("{} does not have a multiplier because they have never earned any {}.".format(person, self._config["currency"]["shorthand"]))
            mp = str(round(self._money_manager.get_multiplier(person), 5))
            if args.raw:
                return mp
            else:
                return "{} has a {} multiplier.".format(person, mp)

        if args.send:
            if message.isInternal():
                return RuntimeError("Can't send money through internal commands.")
            try:
                amount_to_send = float(args.send[0])
            except:
                return ValueError("Could not parse {} into a float".format(args.send[0]))
            sender = message.get_alias()
            reciever = args.send[1]

            if amount_to_send < 0:
                return RuntimeError("Can't send a negative amount of money")

            if self._money_manager.get_amount(sender) < amount_to_send:
                return RuntimeError("Can't send more money than you have.")
            amount_to_send = self._money_manager.float_to_coin(amount_to_send)

            response = self._money_manager.transfer(amount_to_send, sender, reciever)

            self.save()
            return "Sent {amount}{currency} to {person}.".format(amount=amount_to_send, currency=self._config["currency"]["shorthand"], person=reciever)

        if args.amount:
            if not type(args.amount) == str:
                args.amount = message.get_alias()

            if not self._money_manager.has_account(args.amount):
                return KeyError("{} has never earned any {}.".format(args.amount, self._config["currency"]["shorthand"]))
            amount = self._money_manager.get_amount(args.amount)
            if args.raw:

                return str(amount)
            return "{person} has {amnt}{currency}".format(person=args.amount, amnt=amount, currency=self._config["currency"]["shorthand"])
    
        if args.ledger:
            if len(self._money_manager.ledger.keys()) == 0:
                return "No one has any stored money."

            if args.raw:
                ans = ""
            else:
                ans = "Person                                   Amount\n"


            for key in reversed(sorted(self._money_manager.ledger.keys(), key=lambda x: self._money_manager.get_amount(x))):
                ans += "{:40s} {}\n".format(key, self._money_manager.get_amount(key))
            return self._bot.getService("paste").paste(ans, message)

        return self.parser.format_usage()
