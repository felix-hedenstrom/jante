"""
@Author Felix Hedenström
Made PEP8 compliant on 2019-05-17
"""

class Service:
    """
    Create a service that offers methods to other plugins.
    """
    def __init__(self, documentation):
        self._documentation = documentation
        self.__doc__ = self._documentation
        
        self._functions = {}
    
    def get_service_documentation(self):
        return self.__doc__
        
    def get_function_documenation(self, name):
        assert type(name) == str
        return self._functions[name]
        
    def get_function(self, name):
        assert type(name) == str
        
        return self._functions[name][0]
        
    def __getattr__(self, name):
        return self.get_function(name)
        
    def add_function(self, name, func, documentation):
        """
        name: String describing the method name
        
        Adds a method to the service. Must supply a name of the method as well as a breif description of how it works.
        
        Returns true if the method is stored in the object, False if it already exists.
        """
        assert type(name) == str
        assert type(documentation) == str
        
        
        if name in self._functions:
            return False
            
        self._functions[name] = (func, documentation)
        


