#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import urllib.parse
import html
import math
import configparser

if __name__ == '__main__':
    import sys
    sys.path.append('../..')
    sys.path.append('../../libs')

from plugins.parsingplugintemplate import ParsingPluginTemplate
import jantepastedb

from libs.servicemanager.service import Service

class JantePastePlugin(ParsingPluginTemplate):
    def __init__(self, bot): 
        self._config = configparser.ConfigParser()
        self._config.read("plugins/paste/settings.ini")
        
        super(JantePastePlugin, self).__init__(bot,command=self._config.get('paste', 'command', fallback='paste'), description='A pastebin designed to be used with the janteweb feature. Offers the pasting service.')
        
        self.paste_db = jantepastedb.JantePasteDB()
        bot.register_web_route('/paste', self.webparse)
        
        pasting_service = Service("""
                                  Convert long texts into short urls if possible. 
                                  """)
        
        pasting_service.add_function("paste", self.paste , "Give text and the jantemessage that triggered the plugin call and this will extract the text and paste it if necessary. Will not paste if message is internal. If message is None it will always paste")

        self._bot.offer_service("paste", pasting_service)
        
    def paste(self, text, original_message=None):
        """
        Pastes the text in the message and returns the text from the paste.
        
        If it is an internal message, no pasting will occur.
        """
         
        if not self._config.getboolean('paste', 'allow_pasting', fallback=False) or (not original_message == None and type(original_message.getAddress()) == tuple):
            return text
            
        limitchars = 200
        limitlines = 3

        
        if not type(text) == str:
            raise TypeError("Text must be a string. Was \"{}\".".format(type(text)))

        if len(text) < limitchars and len(list(filter(lambda c: "\n" in c, text))) < limitlines:
            return text
            
        return jantepastedb.quickpost(text)
        
    def parse(self, message):
        key = message.get_text()
        if key.strip() == "":
            res = self.paste_db.get_last()
            if res == None:
                return "No paste has been posted."
            return res
        
        if not self.paste_db.contains(key):
            return 'Paste not found.'
        else:
            return self.paste_db.get(key)
            
        return "Must supply argument."
    
    def webparse(self, req):
        mypath = req.path
        raw = False
        
        if mypath.endswith('/raw'):
            raw = True
            mypath = mypath[:-4]
        
        urlprops = urllib.parse.urlparse(mypath)
        qsprops = urllib.parse.parse_qsl(urlprops.query)
        
        key = re.search(r'(?<=\/)[^\/]+$', urlprops.path)
        
        if key != None:
            key = key.group(0)
        
        # add line numbers
        data = list(enumerate(self.paste_db.get(key).split('\n'), start=1))
        
        pagetemplate = """
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8" />
                <title>Jantepaste</title>
                <style type="text/css">
                body {{
                    margin:0px;
                    padding:0px;
                }}
                
                * {{
                    font-size:14px;
                    font-family:'droid sans mono', monospace;
                    color:#fff;
                    background-color:#002b36;
                }}
                
                .linenumbers {{
                    -webkit-user-select:none;
                    -moz-user-select:none;
                    -ms-user-select:none;
                    user-select:none;
                    position:absolute;
                    line-height:18px;
                    width:_NUMWIDTH_px;
                    white-space:pre;
                    float:left;
                    clear:none;
                    color:#999;
                    background-color:#000;
                    padding-left:0px;
                    padding-right:4px;
                    padding-top:4px;
                    padding-bottom:4px;
                }}
                
                .content {{
                    line-height:18px;
                    width:100px;
                    overflow:visible;
                    position:absolute;
                    left:_NUMWIDTH_px;
                    white-space:pre;
                    float:left;
                    clear:none;
                    padding-left:4px;
                    padding-right:0px;
                    padding-top:4px;
                    padding-bottom:4px;
                }}
                </style>
            </head>
            <body>
                <div>{output}</div>
            </body>
        </html>
        """
        
        pagetemplate = pagetemplate.replace('_NUMWIDTH_', str(10 + math.ceil(9 * math.ceil(math.log10(len(data))))))
        pagetemplate = re.sub(r'^\n[ ]{8}', '', pagetemplate)
        pagetemplate = re.sub(r'\n[ ]{8}', '\n', pagetemplate)
        
        if key == None or not self.paste_db.contains(key):
            req.send_http_response_code(404)
            req.send_http_header('Content-type', 'text/plain; charset=utf-8')
            req.send_http_output('Paste not found')
        else:
            req.send_http_response_code(200)
            
            if raw == False:
                req.send_http_header('Content-type', 'text/html; charset=utf-8')
                
                # linetemplate = '<div class="row"><div class="lineno">{}</div><div class="code">{}</div></div><div class="break" />'
                output = list()
                linenums = list()
                contents = list()
                
                for line in data:
                    linenums.append(' ' * (math.ceil(math.log10(len(data))) - math.floor(math.log10(line[0]))) + str(line[0]))
                
                output.append('<div class="linenumbers">{}</div>'.format('\n'.join(linenums)))
                
                for line in data:
                    contents.append('{}'.format(html.escape(line[1])))
                
                output.append('<div class="content">{}</div>'.format('\n'.join(contents)))
                output.append('<div style="float:none; clear:both;"></div>')
                
                output = '\n'.join(output)
                
                req.send_http_output(pagetemplate.format(output=output))
            else:
                req.send_http_header('Content-type', 'text/plain; charset=utf-8')
                req.send_http_output(self.paste_db.get(key))

if __name__ == '__main__':
    from mockbot import mockbot
    from jantemessage import jantemessage
    
    bot = mockbot()
    bot.setConfig('paste', 'command', 'paste')
    
    p = jantepasteplugin(bot)
    
    try:
        f = open('/tmp/jantepaste.html', 'r')
        htmldata = f.read()
        f.close()
    except:
        htmldata = 'hello world'
    
    url = jantepastedb.quickpost(htmldata)
    
    class mockreq:
        def __init__(self, path):
            self.path = path
        
        def __getattr__(self, key):
            print('mockreq noop: {}'.format(key))
            def nofn(*args, **kwargs):
                pass
            
            return nofn
        
        def send_http_output(self, data):
            f = open('/tmp/jantepaste.html', 'w+')
            f.write(data)
            f.close()
    
    p.webparse(mockreq(url))
