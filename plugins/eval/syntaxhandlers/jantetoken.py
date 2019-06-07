from enum import Enum

class identifier:
    def __init__(self, text):
        assert type(text) == str
        self._text = text
    def __repr__(self):
        return "identifier: \"{}\"".format(self._text)
    def __eq__(self, other):
        if not type(other) == identifier:
            return False
        return self._text == other._text
    def __str__(self):
        return self._text

class action:
    class __variable:
        def __init__(self, ident):
            self._identifier = ident

        def __eq__(self, other):
            return type(other) == type(self) and self._identifier == other._identifier
        def __repr__(self):
            return str(self._identifier)
        def getName(self):
            return self._identifier
        def getIdentifier(self):
            return self.getName()
    class variable_assign(__variable):
        def __init__(self, variable, value):
            super().__init__(variable)
            self._value = value
        def __eq__(self, other):
            return super().__eq__(other) and other._value == self._value
        def __repr__(self):
            return "assign({} -> {})".format(super().__repr__(), self._value) 
        
        def getValue(self):
            return self._value
    
    class variable_deref(__variable):
        def __init__(self, variable):
            super().__init__(variable)
        def __repr__(self):
            return "deref({})".format(super().__repr__())
    class suppress:
        def __init__(self):
            pass
        def __eq__(self, other):
            return type(other) == type(self)
        def __repr__(self):
            return "suppress()"

class jantetoken(Enum):
    SUPPRESS       = ";"
    L_BRACKET      = "("
    R_BRACKET      = ")"
    ACTION         = "$"
    ASSIGN         = "="
