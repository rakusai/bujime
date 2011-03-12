# -*- coding:utf-8 -*-

#Google App Engine拡張

import os
import re
import random
import pickle

from google.appengine.api import memcache
from google.appengine.ext import db
from types import *

class SessionData(db.Model):
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)


class Session():
    key = None
    def __init__(self, request, response):
        
        self.key = request.cookies.get('session_id', None)
            
        if not self.key:
            self.reset_key(request, response)
            
    def reset_key(self, request, response):
        #全サブドメイン（裸ドメイン含む）でクッキーを共通にする
        domain = ''
        if os.environ.has_key("SERVER_NAME"):
            match = re.search("\w+\.(com|jp)$",os.environ["SERVER_NAME"]) 
            if match:
                domain = "domain=." + match.group(0) + ";"
        
        self.key = self.create_key()
        response.headers.add_header(
            'Set-Cookie',
            'session_id=%s; %s expires=Fri, 31-Dec-2020 23:59:59 GMT' \
            % (self.key,domain))
        response.headers.add_header(
            'P3P', 
            'CP="CAO PSA OUR"') #P3P コンパクト ポリシー ヘッダー
    
    def create_key(self):
        keys = '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ'
        session_key = ""
        for i in xrange(32):
            session_key += random.choice(keys)
        
        return session_key
        
    def get_key(self):
        return self.key

    def set(self,name,val):        
        key = self.get_key() + "//" + name
        memcache.set(key, val, 28*60*60*24)
        sd = SessionData.get_or_insert(key)
        if sd is None or sd.content != val:
            sd.content = val
            sd.put()
        
    def get(self,name,default=''):        
        key = self.get_key() + "//" + name
        result = memcache.get(key)
        if result is not None:
            return result
            
        sd = SessionData.get_by_key_name(key)
        if sd is not None and sd.content:
            val = sd.content
            memcache.set(key, val, 28*60*60*24)
            return val

        return default
        
    def delete(self,name):
        key = self.get_key() + "//" + name
        memcache.delete(key)
        sd = SessionData.get_by_key_name(key)
        if sd:
            sd.delete()
    
