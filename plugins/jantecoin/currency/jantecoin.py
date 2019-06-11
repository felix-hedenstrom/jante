"""
Author: Felix H
Used by the JanceCoinPlugin as currency.
Uses integers make sure the count of the currency is accurate.


Can only be saved using jsonpickle
"""

PARTS_IN_WHOLE = 100
"""
def JanteCoinFactory(_str, parts_in_whole=PARTS_IN_WHOLE):
    
    partitioning = _str.split(".")
    if len(partitioning) > 2:
        raise ValueError("Can't contain more than one \".\"")
    
    try:
        whole = int(partitioning[0])
    except:
        raise ValueError("Can't parse {} into an integer.".format(partitioning[0]))
    if len(partitioning) == 1:
        part = 0
    else:
        try:
            part = int(partitioning[1])
        except:
            raise ValueError("Can't parse {} into an integer.".format(partitioning[1]))
    
    if part >= parts_in_whole:
        raise ValueError("The part after the decimal mark can't be larger than {}. Was {}.".format(parts_in_whole - 1, part)) 
    
    return JanteCoin(whole, part, parts_in_whole)
"""    
import re

class JanteCoin(object):
    """
    wholes: How many counts of the currency there are
    parts: How many parts there are of the currency. 100 parts make a whole. 
    """
    def __init__(self, wholes, parts=0, parts_in_whole=PARTS_IN_WHOLE):
        if not isinstance(wholes, int):
            raise ValueError("wholes must be an integer. was a {}.".format(type(wholes)))
        if not isinstance(parts, int):
            raise ValueError("parts must be an integer.")
        if parts < 0:
            raise ValueError("Parts can't be a negative number. Was {}".format(parts))
        if parts >= parts_in_whole:
            raise ValueError("Expected parts lower than {}, was {}".format(parts_in_whole, parts))
        if wholes < 0:
            raise ValueError("Can't be negative number.")
            
        self._wholes = wholes
        self._wholes = wholes
        self._parts = parts
        self._parts_in_whole = parts_in_whole
        
    def __str__(self):
        base = "{}.{}{}".format(self._wholes,  "0" * (len(str(self._parts_in_whole)) - len(str(self._parts)) - 1), self._parts)
        #print(base)
        # transform 1.00000 -> 1
        base = re.sub(r"\.0+$", "", base)
        
        
        # transform 1.010 -> 1.01
        base = re.sub(r"(\.0*[^0]+)0+$", r"\1", base)
        return base
    
    def __repr__(self):
        return "({}) with max={}".format(str(self), self._parts_in_whole)
        #return "{}.{} with max={}".format(self._wholes, self._parts, self._parts_in_whole)
        
    def __eq__(self, other):
        if not isinstance(other,JanteCoin):
            return False
        return other._wholes == self._wholes and other._parts == self._parts
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __lt__(self, other):
        if type(other) == float or type(other) == int:
            if self._wholes < int(other):
                return True
            return self._wholes == int(other) and self._parts < (other % 1.0) * self._parts_in_whole
            
        if self._wholes < other._wholes:
            return True
        return self._wholes == other._wholes and self._parts < other._parts 
        
    def __rmul__(self, other):
        return self.__mul__(other)
    def to_float(self):
        return self._wholes + (float(self._parts) / self._parts_in_whole)
            
    def __mul__(self, other):
        
        if not (isinstance(other, int) or isinstance(other, float)):
            raise TypeError("Cannot multiply by anything other than an int or a float.")
        
        wholes = self._wholes * other
        
        parts = int(self._parts_in_whole * (wholes % 1.0))
        
        parts += self._parts * other
        
        if parts >= self._parts_in_whole:
            wholes += parts // self._parts_in_whole
            parts = parts % self._parts_in_whole
        
        return JanteCoin(int(wholes), int(parts), parts_in_whole=self._parts_in_whole)
    
    def __sub__(self, other):
        if not type(other) == JanteCoin:
            raise TypeError("Can only subtract another JanteCoin.")
            
        wholes = self._wholes - other._wholes
        
        
        parts = self._parts - other._parts
        
        if parts < 0:
            wholes += -parts // self._parts_in_whole - 1
            parts %= self._parts_in_whole 
        
        if wholes < 0:
            raise ValueError("Can't handle negative numbers.")
        return JanteCoin(wholes, parts, parts_in_whole=self._parts_in_whole)
        
    def __add__(self, other):
        if not type(other) == JanteCoin:
            raise TypeError("Can only add to another JanteCoin.")
        wholes = self._wholes + other._wholes
        parts = self._parts + other._parts
        
        if parts >= self._parts_in_whole:
            wholes += parts // self._parts_in_whole
        
        parts %= self._parts_in_whole
        
        
        return JanteCoin(wholes, parts, parts_in_whole=self._parts_in_whole) 
    
    
        