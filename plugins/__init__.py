#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def import_all(config):
    import os
    
    for module in os.listdir(os.path.dirname(__file__)):
        # If using blacklist and module is blacklisted
        if config.getboolean('plugins', 'use_blacklist') and module in config['plugins']['blacklist']:
            continue
        # IF using whitelist and module is not whitelisted
        if config.getboolean('plugins', 'use_whitelist') and not module in config['plugins']['whitelist']:
            continue
        
        if module == "plugintemplate.py" or module == "parsingplugintemplate.py" or module =='__init__.py':
            continue
        
        for submod in os.listdir(os.path.dirname(__file__) + "/" + module):
            if not submod[-3:] == '.py' or submod == '__init__.py':
                continue
            
            ans = "{}.{}".format(module, submod[:-3])
            __import__(ans, globals(), locals(), level=1)
    
    del module
    del os
