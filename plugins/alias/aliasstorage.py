"""
@Author FelixH
"""



import json
import threading

class AliasStorageManager():
    """
    Stores and manages aliases.
    Makes sure that aliases can't be stolen from other accounts
    Example:
    
        a = aliasstorage()
        a.exists("fb") # False
        a.newAlias("fb", "foobar") # True
        a.newAlias("fb", "baarfoo") # False
        
        a.getOwner("fb") # "foobar"
        a.addAlias("fb", "baarfoo", "coofar") # False
        a.addAlias("fb", "baarfoo", "foobar") # True
    """
    
    def __init__(self, base_path, filename):
        
        if base_path == None:
            self._path_accountaliases = "/tmp/accountaliases.json"
            self._path_aliasowners = "/tmp/aliasowners.json"
        else:
            
            self._path_accountaliases = "{}{}.account.json".format(base_path, filename)
            self._path_aliasowners = "{}{}.owners.json".format(base_path, filename) 
        
        
        self._mutex = threading.Lock()
        
        with self._mutex:
            try:
                with open(self._path_accountaliases) as f:
                    self._accountaliases = json.load(f) 
            except:
                self._accountaliases = {}
        
            try:
                with open(self._path_aliasowners) as f:
                    self._aliasowners = json.load(f) 
            except:
                self._aliasowners = {}
    
    # Returns any alias associated with the account
    def get_alias(self, account):
        if not account in self._accountaliases:
                return None
        
        return self._accountaliases[account]
    #TODO implement this
    def remove_account(self):
        raise NotImplementedError("This method is not yet implemented.")
        
    # Creates a new alias for the account.
    # Can only create aliases that do not already exists.
    # If alias was created successfully, return True
    # Otherwise, return False
    def new_alias(self, alias, account):
        if not type(alias) == str:
            raise ValueError("alias must be a string.")
        if not type(account) == str:
            raise ValueError("account must be a string.")    
        
        if alias in self._aliasowners:
            return False
            
        with self._mutex:
            self._aliasowners[alias] =  [account]
            self._accountaliases[account] = alias
        self.save()
        return True
        
    # Checks if alias exists    
    def exists(self, alias):
        return alias in self._aliasowners
    
    # Returns the owner of an alias.
    # If alias doesn't exist, return an empty list.
    def get_owners(self, alias):
        if not alias in self._aliasowners:
            return []
        return self._aliasowners[alias]
        
    # Adds another account to the alias.
    # Only works if the owner of the alias is adding the new account
    # Returns True if account successfully added to alias
    # False otherwise
    def add_alias(self, alias, opaccount, accounttoadd):
        if not opaccount in self.getOwners(alias):
            return False
        with self._mutex:
            self._accountaliases[accounttoadd] = alias
            self._aliasowners[alias] += [accounttoadd]
        self.save()
        return True
        
    def save(self):
        with self._mutex:
            with open(self._path_accountaliases, "w") as f:
                json.dump(self._accountaliases, f)
            with open(self._path_aliasowners, "w") as f:
                json.dump(self._aliasowners, f)
