try:
    from jantetoken import jantetoken, identifier, action
except:
    from plugins.eval.syntaxhandlers.jantetoken import jantetoken, identifier, action

maxdepth = 10

import re



class parser:
    def __init__(self):
        pass
    def find_token(self, tokens, token):
        for i in range(0, len(tokens)):
            if tokens[i] == token:
                return i
        return None
        
    def find_closing_bracket(self, tokens):
        bracket_count = 1

        for i in range(0,len(tokens)):

            if tokens[i] == jantetoken.L_BRACKET:
                bracket_count += 1
            elif tokens[i] == jantetoken.R_BRACKET:
                bracket_count -= 1
            if bracket_count == 0:
                return i

        raise RuntimeError("Expected balanced brackets but seems unbalanced. Tokens: {}".format(tokens))

    def __second_pass(self, tree):
        """bbq sandwich
        Find all variable assignments and dereferations
        """
        lasttoken = None
        for i in range(0, len(tree)):
            if tree[i] == jantetoken.ASSIGN:
                pass
        return tree

    def parse(self, tokens, depth=0):
        if depth > maxdepth:
            raise ValueError("Too deep. Cannot exceed {} nested commands.".format(maxdepth))
        if not len(list(filter(lambda x: x == jantetoken.L_BRACKET, tokens))) == len(list(filter(lambda x: x == jantetoken.R_BRACKET, tokens))):
            raise ValueError("Unbalanced bracets.")
        tree = []
        # +1 for every leftbracket and -1 for every right
        bracketcount = 0
        lasttoken = None
        i = 0
        while(i < len(tokens)):
            if tokens[i] == jantetoken.L_BRACKET:
                if not lasttoken == jantetoken.ACTION:
                    raise ValueError("Unescaped left bracket.")
                closing_index = self.find_closing_bracket(tokens[i + 1:]) + i + 1
                subtree = self.parse(tokens[i + 1:closing_index], depth + 1)
                i = closing_index
                if subtree == []:
                    raise RuntimeError("Evaluated {} to an empty token".format(tokens[i+1:closing_index]))
                tree.append(subtree)
            
            elif tokens[i] == jantetoken.ASSIGN:
                """
                Assign a variable
                must be formed
                variable_name = $(expression)
                where expression can be as deep as maxdepth allows.
                """
                
                
                
                if not type(lasttoken) == identifier:
                    raise ValueError("Can only assign variables.")
                
                lasttoken = str(lasttoken).strip()
                
                if not re.match(r"^[A-Za-z\_][\w\d\-\_]*$", lasttoken):
                    raise ValueError("Variables must start with a letter and can only contain letters, numbers and -_. The variable \"{}\" did not.".format(lasttoken))
                
                # Remove the identifier
                tree = tree[:-1]
                
                startindex = i + 1
                suppress_index = self.find_token(tokens[startindex:], jantetoken.SUPPRESS) 
                
                if suppress_index == None:
                    raise ValueError("Must end declerations of variables with \"{}\". Possible unescaped \"=\".".format(jantetoken.SUPPRESS.value))
                
                suppress_index += + startindex
                
                subtree = self.parse(tokens[startindex:suppress_index], depth + 1)[0]
                if type(subtree) == str:
                    subtree = [subtree]
                
                if subtree == []:
                    raise RuntimeError("Evaluated {} to an empty token".format(tokens[i+1:closing_index]))
                
                i = suppress_index
                
                tree.append(action.variable_assign(lasttoken, subtree))
                
            elif type(tokens[i]) == identifier:
                if lasttoken == jantetoken.ACTION:
                    parts = str(tokens[i]).split(" ")
                    tree.append(action.variable_deref(parts[0].strip()))
                    if len(parts) > 1:
                        tree.append(" {}".format(" ".join(parts[1:])))
                    
                
                else:
                #assert type(tokens[i]) == identifier, "Was type {}".format(type(tokens[i]))
                    tree.append(str(tokens[i]))
            
            elif tokens[i] == jantetoken.SUPPRESS: 
                tree.append(action.suppress())
            
            elif not tokens[i] == jantetoken.ACTION:
                raise RuntimeError("Parser failed on token {}".format(tokens[i]))
            
            lasttoken = tokens[i]
            i += 1


        tree = self.__second_pass(tree)

        return tree
