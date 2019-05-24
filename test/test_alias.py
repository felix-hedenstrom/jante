import util.base_test

class TestAlias(util.base_test.BaseTest):
    def test_plugin_disabled(self):
        self._config['global']['use_aliases'] = "False"
        self.assertEqual(self.eval("!alias --my-alias", sender="alice"), "Aliases are not in use. This plugin should probably be disabled.")

    def test_no_alias(self):
        self._config['global']['use_aliases'] = "True"
        
        #Evaluator does not have enough functionallity to properly test alias
        #self.assertEqual(self.eval("!alias --my-alias", sender="alice"), "@alice")
