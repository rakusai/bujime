# -*- coding: utf-8 -*-

import sys

import cgi
import os
import datetime
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api.datastore_errors import Timeout
from google.appengine.api.labs import taskqueue

from django.utils import simplejson 

import yaml
import urllib
from urllib import quote
from urllib import unquote
import re
import random
import math
import md5
import logging
import base64

sys.path.append('lib')

from session import Session


class BasePage(webapp.RequestHandler):
    
    session = None #sessionを拡張
    user = None #現在のユーザー

    def initialize(self,request, response):
        webapp.RequestHandler.initialize(self,request, response)
        self.session = Session(request, response)
        self.get_current_user()

    def add_password(self, user, password):
        self.auth_list.append({'user':user,'pass':password})



    def render_json(self, result):
        self.response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
        callback = re.sub("[^\w\d]","",self.request.get('callback'))
        if callback:
            self.response.out.write(callback + "(")

        simplejson.dump(result,self.response.out, ensure_ascii=False)

        if callback:
            self.response.out.write(");")

    def render(self,path,params):
        if not params:
            params = dict()
        
        static_domain = ''
        domain = ''
        app_version = os.environ.get("CURRENT_VERSION_ID","")
        
        domain = os.environ.get("SERVER_NAME","")
        
        if domain != "www.caffein.tv":
            app_version = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        
        params["app_version"]   = app_version
        params["user"] = self.user

        #username
        username = self.get_username()
        params["username"] = username
        
        path = os.path.join(os.path.dirname(__file__), path)
        self.response.out.write(template.render(path, params))

    def logout(self):
        self.session.set("userkey","")
        self.session.set("username","")
        #セッションIDの振り直し（セキュリティ上重要！）
        self.session.reset_key(self.request, self.response)
        
        
    def get_userkey(self):
        if self.user:
            userkey = self.user.key().name()
        else:
            userkey = "session:" + self.session.get_key()
        return userkey

    def get_username(self): 
        username = self.session.get("username")
        if not username and self.user:
            username = self.user.username
        if not username:
            username = ""
        return username
        
    def get_current_user(self):
        userkey = self.session.get("userkey")
        self.user = None
        if userkey:
            person = memcache.get(userkey)
            if not person:
                person = Person.get_by_key_name(userkey)
                memcache.set(userkey,person,20*24*60*60)
            if person:
                self.user = person
                return True

    def init_pagenation(self):
        try:
            return int(self.request.get('page',1))
        except:
            return 1

    def make_pagenation(self,page,total):
        prev = False
        next = False
        if page > 1:
            prev = True
            
        if int(page) < int(total):
            next = True
            
        #?以降のクエリー（URL）を作成
        query_string = self.request.query_string
        
        def get_url(page,query_string):
            match = re.search("page=[0-9]*",query_string)
            if match:
                url = re.sub("page=[0-9]*","page="+str(page),query_string)
            else:
                if len(query_string) > 0:
                    query_string = re.sub("&?$","&",query_string)
                url = query_string + "page="+str(page)
            return self.request.path + "?" +  url # + "#info_bar"
            
        prev_url = get_url(page-1,query_string)
        next_url = get_url(page+1,query_string)

        content = ''
        pgrange = 9
        for i in xrange(max(1,page-pgrange), page):
            content += '<a href="' + get_url(i,query_string) + '">' + str(i) + '</a> '
        content += '<span class="selected">' + str(page) + '</span> '
        for i in xrange(page+1, min(page+pgrange,total)+1):
            content += '<a href="' + get_url(i,query_string) + '">' + str(i) + '</a> '
#        prev_url = self.request.path + "?" +  prev_url
#        next_url = self.request.path + "?" +  next_url
        
        pages = {
            "show" :int(total) > 1,
            "page":page, 
            "total_pages":total,
            "prev":prev,
            "next":next,
            "content": content,
            "prev_url":prev_url,
            "next_url":next_url,
            "prev_page":page-1,
            "next_page":page+1,
            }
        
        return pages
