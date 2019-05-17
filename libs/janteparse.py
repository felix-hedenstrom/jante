import argparse
class ArgumentParserError(Exception):
    pass

class JanteParser(argparse.ArgumentParser):
    
    def error(self, message):
        raise ArgumentParserError(self.format_usage() + message)
