"""
@Author Felix Hedenström
"""

from libs.servicemanager.service import Service 

class ServiceManager:
    def __init__(self):
        self._services = {}
        
    def offer_service(self, service_name, serv):
        assert type(service_name) == str
        assert type(serv) == Service
        if service_name in self._services:
            return False
            
        self._services[service_name] = serv
        
    def __getattr__(self, name):
        return self.get_service(name)
    
    def get_service(self, name):
        assert type(name) == str
        return self._services[name]
                
    
