import unittest

from lexer import lexer
from jantetoken import jantetoken, identifier, action
from parser import parser
import copy



class TestLexer(unittest.TestCase):


    def test_base(self):
        l = lexer()
        lex_input = "!roll $(!list music)"
        self.assertEqual([identifier("!roll "), jantetoken.ACTION, jantetoken.L_BRACKET, identifier("!list music"), jantetoken.R_BRACKET], l.lex(lex_input))
    def test_empty(self):
        l = lexer()
        lex_input = ""
        self.assertEqual([], l.lex(lex_input))

    def test_escape(self):
        l = lexer()
        test_input = "!say :\)"
        self.assertEqual([identifier("!say :)")], l.lex(test_input))

    def test_escape2(self):
        l = lexer()
        test_input = "!echo $(!say I think !top is :\()"
        self.assertEqual([identifier("!echo "), jantetoken.ACTION, jantetoken.L_BRACKET, identifier("!say I think !top is :("), jantetoken.R_BRACKET],
            l.lex(test_input))

    def test_escape_dollar(self):
        l = lexer()
        test_input = "!echo i need \$4."
        self.assertEqual([identifier("!echo i need $4.")], l.lex(test_input))

    def test_empty_subcommand(self):
        l = lexer()
        test_input = "!echo $()"
        self.assertEqual([identifier("!echo "), jantetoken.ACTION, jantetoken.L_BRACKET,jantetoken.R_BRACKET], l.lex(test_input))
    def test_double_subcommand_seperated_by_whitespace(self):
        l = lexer()
        test_input = "!echo I want to have a $(!foo) $(!bar)"
        self.assertEqual([identifier("!echo I want to have a "), jantetoken.ACTION, jantetoken.L_BRACKET, identifier("!foo"), jantetoken.R_BRACKET, identifier(" "), jantetoken.ACTION, jantetoken.L_BRACKET, identifier("!bar"), jantetoken.R_BRACKET], l.lex(test_input))
    
    def generate_newline_tokens():
        l = lexer()
        test_input = """
                        !echo
                        $(
                            !roll
                            $(
                                 !list yrke
                            )
                        )

                     """
        return l.lex(test_input)

    def test_newlines(self):

        self.assertEqual([identifier(" !echo "), jantetoken.ACTION, jantetoken.L_BRACKET, identifier(" !roll "), jantetoken.ACTION, jantetoken.L_BRACKET, identifier(" !list yrke "), jantetoken.R_BRACKET, jantetoken.R_BRACKET], TestLexer.generate_newline_tokens())

    def test_suppress(self):
        l = lexer()
        test_input = "!echo This  ;   !echo That"

        self.assertEqual([identifier("!echo This "), jantetoken.SUPPRESS, identifier(" !echo That")], l.lex(test_input))
    def test_assign(self):
        l = lexer()
        test_input = "x = !echo foo"
        self.assertEqual([identifier("x "), jantetoken.ASSIGN, identifier(" !echo foo")], l.lex(test_input))
        
    def test_deref(self):
        l = lexer()
        test_input = "x = $(!echo foo); $x"
        self.assertEqual([identifier("x "), jantetoken.ASSIGN, jantetoken.ACTION, jantetoken.L_BRACKET, identifier("!echo foo"), jantetoken.R_BRACKET, jantetoken.SUPPRESS, jantetoken.ACTION, identifier("x")], l.lex(test_input))

class TestParser(unittest.TestCase):

    def test_base(self):
        l = lexer()
        p = parser()
        test_input = "!roll $(!list music)"

        self.assertEqual(["!roll ", ["!list music"]], p.parse(l.lex(test_input)))
        
    def test_base2(self):
        l = lexer()
        p = parser()
        test_input = "!echo test"
        
        self.assertEqual(["!echo test"], p.parse(l.lex(test_input)))

    

    def test_deep(self):
        l = lexer()
        p = parser()
        test_input = "!roll $($($($($(!list music)))))"
        tokens = l.lex(test_input)
        self.assertEqual(["!roll ", [[[[["!list music"]]]]]], p.parse(tokens))
    def test_newlines(self):
        p = parser()
        tokens = TestLexer.generate_newline_tokens()
        self.assertEqual([" !echo ", [" !roll ", [" !list yrke "]]], p.parse(tokens))
    def test_unbalanced(self):
        l = lexer()
        p = parser()
        test_input = "!roll $(!list test))"
        tokens = l.lex(test_input)
        with self.assertRaises(ValueError):
            p.parse(tokens)
            
    def test_suppress(self):

        l = lexer()
        p = parser()
        test_input = "!echo Foo; !echo Bar"
        tokens = l.lex(test_input)

        self.assertEqual(["!echo Foo", action.suppress(), " !echo Bar"], p.parse(tokens))

    def test_assign(self):
        l = lexer()
        p = parser()
        tokens = l.lex("x = $(!echo foo); !echo $x")

        self.assertEqual([action.variable_assign("x", ["!echo foo"]), " !echo ", action.variable_deref("x")], p.parse(tokens))
    def test_variable(self):
        l = lexer()
        p = parser()
        tokens = l.lex("x = $(!echo foo); !echo $x")
        self.assertEqual([action.variable_assign("x", ["!echo foo"]), " !echo ", action.variable_deref("x")], p.parse(tokens))
    
    def test_variable(self):
        l = lexer()
        p = parser()
        tokens = l.lex("x = !echo foo; !echo $x")
        self.assertEqual([action.variable_assign("x", [" !echo foo"]), " !echo ", action.variable_deref("x")], p.parse(tokens))
        
    def test_advanced_variables(self):
        test_input = "x = $(!roll); !echo $(y = $(!roll 10); $(!calc --only-answer $x + $y))"
        l = lexer()
        p = parser()
        tokens = l.lex(test_input)
        self.assertEqual([action.variable_assign("x", ["!roll"]), " !echo ", [action.variable_assign("y", ["!roll 10"]), ["!calc --only-answer ", action.variable_deref("x"), " + ", action.variable_deref("y")]]]
                        , p.parse(tokens))

    def test_variable_name1(self):
        l = lexer()
        p = parser()
        tokens = l.lex("_test = $(!echo foo);")
        
        self.assertEqual([action.variable_assign("_test", ["!echo foo"])], p.parse(tokens))
    def test_variable_name2(self):
        l = lexer()
        p = parser()
        tokens = l.lex("1test = $(!echo foo)")
        
        
        
        with self.assertRaises(ValueError):
            p.parse(tokens)

        tokens = l.lex("föö' = $(!echo foo)")
        
        with self.assertRaises(ValueError):
            p.parse(tokens)

        tokens = l.lex("test = !echo foo")
        
        with self.assertRaises(ValueError):
            p.parse(tokens)
            
    def test_deref(self):
        l = lexer()
        p = parser()
        tokens = l.lex("test = $(!echo foo); $test")
        self.assertEqual([action.variable_assign("test", ["!echo foo"]), action.variable_deref("test")], p.parse(tokens))
    
    def test_bad_equals(self):
        l = lexer()
        p = parser()
        tokens = l.lex("things = bad")
        with self.assertRaises(ValueError):
            p.parse(tokens)
    def test_double_subcommand_seperated_by_whitespace_parser(self):
        l = lexer()
        p = parser()
        tokens = l.lex("!foo $(!bar) $(!baz)")
        self.assertEqual(["!foo ", ["!bar"], " ", ["!baz"]], p.parse(tokens) )
        
if __name__ == '__main__':
    unittest.main()
