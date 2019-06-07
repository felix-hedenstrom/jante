try:
    from jantetoken import jantetoken, identifier
except:
    from plugins.eval.syntaxhandlers.jantetoken import jantetoken, identifier
escapechar = "\\"

import re

class lexer:
    """
    Translates text into jantetokens and identifiers.
        Example
            !roll $(!list things)
        Will create the array
            [identifier("!roll"), jantetoken.ACTION, jantetoken.L_BRACKET, identifier("!list things"), jantetoken.R_BRACKET]

    Brackets and the symbol "$" that are used in a way that is used in a way such that it should not be parsed as such should be
    escaped with the "\" character.

        Example
            !roll $(!list :\))
        Gives
            [identifier("!roll"), , jantetoken.ACTION, jantetoken.L_BRACKET, identifier("!list :)"), jantetoken.R_BRACKET]
    """
    def __init__(self):
        return
    def lex(self, text):
        tokens = []
        tmp = ""
        lastchar = None
        text = re.sub(r"\s+", " ", text)


        for c in text:
            if lastchar == escapechar:
                tmp += c
                
            else:
                addedToken = False

                for jt in jantetoken:
                    if c == jt.value:
                        if not tmp.strip() == "" or jt == jantetoken.ACTION and tokens[-1] == jantetoken.R_BRACKET:
                            tokens.append(identifier(tmp))
                        
                        tmp = ""
                        addedToken = True
                        tokens.append(jt)
                if addedToken == False and not c == escapechar:
                    tmp += c

            lastchar = c
        if not tmp.strip() == "":
            tokens.append(identifier(tmp))


        #tokens = list(filter(lambda x: not re.match("^\s*$", str(x)) if type(x) == identifier else True, tokens))
        #assert len(list(filter(lambda x: type(x) == identifier and str(x) == "", tokens))) == 0, tokens





        return tokens
