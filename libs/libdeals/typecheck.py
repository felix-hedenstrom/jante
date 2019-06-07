#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def instanceof(val, _type, name=None):
    if not isinstance(val, _type):
        if name != None:
            name = ' for \'{}\''.format(name)
        
        raise Exception('{} is not a valid type{} (must be instance of {})'.format(type(val), name, _type))
    else:
        return val

def single_type(val, _type, name=None):
    if type(val) != _type:
        if name != None:
            name = ' for \'{}\''.format(name)
        
        raise Exception('{} is not a valid type{} (must be {})'.format(type(val), name, _type))
    else:
        return val

def fn_apply(val, f, name=None, suggest=None):
    """
    fn_apply: type validation by function application. applies given function to given value
              and returns the result. if an exception occurs during the function call (e.g
              a call to int(x) fails with exception) the type of the given value is taken to
              be invalid and an exception is be raised.
    
    example:
    
    def foo(bar):
        bar = typecheck.fn_apply(bar, lambda x: str(x), name='bar', suggest=str)
    
    """
    
    e = None
    
    try:
        return f(val)
    except:
        if name != None:
            name = ' for \'{}\''.format(name)
        
        if suggest != None:
            suggest = ' (suggested: {})'.format(str(suggest))
        
        e = Exception('{} is not a valid type{}{}'.format(type(val), name, suggest))
    
    raise e
