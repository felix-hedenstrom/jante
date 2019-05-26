"""
@Author Felix Hedenström

Offers a service that allows a user to have multiple accounts that are treated as one.
Useful for the basic account-restricted features in jantecoin, list and so on.

TODO
    * Allow aliases to be removed
    * Port to (j)argparse
"""

import shlex, getopt

import threading
import configparser
import re

from libs.servicemanager.service import Service
from plugins.parsingplugintemplate import ParsingPluginTemplate
from plugins.alias.aliasstorage import AliasStorageManager 


class AliasManagerPlugin(ParsingPluginTemplate):
    """
    alias
        Manages aliases.
        
            (-h, --help)
                Shows this.
            
            (--my-alias)
                See your own alias.
                
            (-c, --create) <alias>
                Create an alias. The current account becomes the owner of that alias. Sets <alias> as the
                accounts alias.
        
            (-a, --accept) <alias>
                Accept an alias. If an aliasowner adds an account as part of that alias, 
                the account has to accept it.
            
            
            !(-r, --remove)
            !    Removes any alias associated with your account.
            !
            
            (--owners) <alias>
                Show the owners of <alias>.
                
            (--exists) <alias>
                Checks if alias exists.
                
            (-p, --pending)
                See pending accepts
        Nonopts:
            add <user> to <alias>
            
            Example:
                add user97 to coolguy100
            
            Makes account specified in <user> use the <alias> as an alias.
            The user then have to accept it by using the (-a, --accept) command.
            
            
    """
    def __init__(self, bot): 
        self._config = configparser.ConfigParser()
        self._config.read("plugins/alias/settings.ini")

        super().__init__(bot, command=self._config.get('alias','command', fallback='alias'), description="Configure the alias of the user if this feature is enabled.")
        
        # Syntax for the base way of adding an alias
        self._regex = "^\s*[aA][dD]{2}\s+([\w\-\_]+)\s+[tT][oO]\s+([\w\-\_]+)\s*$"
        self._mutex = threading.Lock()        
        
        self._manager = AliasStorageManager(self._bot.get_base_data_path(), self._config.get('alias', 'filename', fallback='aliases'))
            
        self._pendingaccepts = []

        
        aliasing_service = Service("""
                                  Create aliases for users. 
                                  """)

        aliasing_service.add_function("get_alias", self.get_alias , "Get the alias of a sender.")
        
        self._bot.offer_service("alias", aliasing_service) 

    def parse(self, message):
        #TODO port to jargparse
        if not self._bot.get_config().getboolean('global', 'use_aliases'):
            return "Aliases are not in use. This plugin should probably be disabled."
            
        argv = shlex.split(message.get_text())
        response = ""
        
        try:
            opts, nonopts = getopt.getopt(argv, 'hc:a:p',
            ["help", "my-alias", "create=", "accept=", "owners=", "exists=", "pending"])
        except:
            return "Not a valid option. Please try another or check out {prefix}{command} --help.".format(prefix=self._bot.get_config().get('global','prefix'), command=self._bot.get_config().get('alias','command'))
        
            
        for opt in opts:
            
            if opt[0] == '-h' or opt[0] == '--help':
                return self._bot.paste(self.__doc__)
                
            if opt[0] == '--my-alias':
                return message.get_alias()
                
                
            if opt[0] == '-c' or opt[0] == '--create':
                if len(opt[1]) < int(self._config.get('alias', 'min_alias_length', fallback=3)):
                    return "Alias must be at least {} characters long.".format(self._config.get('alias','min_alias_length', fallback=3))
                if not self._manager.new_alias(opt[1].strip(), message.get_sender()):
                    return 'Can\'t create alias "{}". Does it already exist?'.format(opt[1])
                
                return 'Created alias "{}". It is now your alias.'.format(opt[1].strip())
            
            if opt[0] == '--owners':
                owners = self._manager.getOwners(opt[1])
                if len(owners) == 0:
                    return 'Alias "{}" does not exists.'.format(opt[1])
                return "{}.".format(", ".join(owners))
                
            if opt[0] == '--exists':
                if self._manager.exists(opt[1]):
                    return 'Alias "{}" exists.'.format(opt[1])
                return 'Alias "{}" does not exist.'.format(opt[1])
                
            if opt[0] == '--pending' or opt[0] == '-p':
                if len(self._pendingaccepts) == 0:
                    return "There are no pending accepts."
                ans = ""
                for pa in self._pendingaccepts:
                    ans += 'Waiting for "{}" to accept alias "{}".\n'.format(pa[0], pa[1])
                return self._bot.paste(ans)
            
            if opt[0] == '--accept' or opt[0] == '-a':
                account = message.get_sender()
                for i in range(len(self._pendingaccepts)):
                    pa = self._pendingaccepts[i]
                    if pa[0] == account:
                        if pa[1] == opt[1]:
                            if self._manager.addAlias(opt[1], pa[2], account):
                                return 'Successfully added alias "{}" to account "{}".'.format(opt[1], account)
                                del self._pendingaccepts[i]
                            else:
                                return 'Could not add account "{}" to alias "{}". Error code 2.'.format(account, opt[1])
                                
                return 'Did not find any pening invitations to alias "{}" and account "{}"'.format(opt[1], account)
            
            return "Something went wrong in alias. Error code 1."
        if len(nonopts) > 0:
            text = " ".join(nonopts)
            
            matching = re.match(self._regex, text)
            if matching == None:
                return 'Couldn\'t parse nonopts. Must be in form "add <user> to <alias>".'
            alias = matching.group(2)
            #print(alias)
            account = matching.group(1)
            owners = self._manager.getOwners(alias)
            if not message.get_sender() in owners:
                if len(owners) == 0:
                    return "Alias \"{}\" does not exists.".format(alias) 
                return "You are not a owner of the alias \"{}\".".format(alias)
            self._pendingaccepts += [(account, alias, message.get_sender())]
            return 'Added pending invitation to alias "{}". Waiting for account "{}" to accept.'.format(alias, account)
            
            
        return "Must specify an option. Use {}{} --help to see see options.".format(self._bot.get_config().get('global', 'prefix'), self._config.get('alias','command', fallback="alias"))
        
    def get_alias(self, sender):
        if not type(sender) == str:
            raise ValueError("Sender must be a string. Was a {}.".format(type(sender)))
        ans = self._manager.get_alias(sender)
        if ans == None:
            return "{}{}".format(self._config.get('alias', 'real_name_prefix', fallback="@"), sender)
        return "{}{}".format(self._config.get('alias', 'alias_prefix', fallback="#"), ans) 
        
