# -*- coding: utf-8 -*-

## /reg?username=<NAME>&identity=<CirrusID>
## usernameのidentityを更新
## 自分以外のidentityを返す

#pre import
execfile("pre_import.py")

#controllers
from controllers.room import *
from controllers.chat import *
from controllers.login import *
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
import urllib

def getjson(q):
        sql = "" #"select * "
        sql = urllib.quote(sql)
#        url = "http://spreadsheets.google.com/tq?key=twenqTTEoUUigkPWhKdHhUA&tq=" + sql

#        res = memcache.get("cache")
#        if not res:
        url = "http://spreadsheets.google.com/tq?key=tgjMrXxdYuNdW0JEMBi36bA"
        result = urlfetch.fetch(url)
        res  = result.content
#            memcache.set("cache",res,20)
            
#        return
        res = res.replace("google.visualization.Query.setResponse(","")
        res = re.sub("\)\;$","",res)
        res = res.replace("yyyy/MM/dd H:mm:ss","")
        res = res.replace("#0.###############","")
        res = re.sub("('style'\:\'[^\']+\')","",res)
        res = re.sub("new Date\(([\d\,]+)\)","'\\1'",res)
#        res = re.sub("new Date\(([\d]+),([\d]+),([\d]+),([\d]+),([\d]+),([\d]+)\)","'\\1/\\2/\\3 \\4:\\5:\\6'",res)
#        res = re.sub("(,p\:[^\}]+})","",res)
        res = re.sub("([{,])([a-zA-Z]+)\:","\\1'\\2':",res)
        res = re.sub(":([0-9]+)\.[0-9]+",":'\\1'",res) #小数点
        res = res.replace('"','')
        res = res.replace("'",'"')
        logging.info(res)
#        return
#        self.response.out.write(res)
#        return
#        self.response.out.write(res)
#        logging.info(res)
       # res = '{"name": "John Smith", "age": 33}'
        
        json = simplejson.loads(res)
        logging.info(json)
        
        newrows = []
        
        logging.info(json["table"]["rows"])
        rows = json["table"]["rows"]
        for row in rows:
            logging.info(row["c"][0]["v"])
            logging.info(row["c"][1]["v"])
            logging.info(row["c"][2]["v"])
            newrows.append({
            "time" : row["c"][0]["f"],#ここだけf
            "pref" : row["c"][1]["v"],
            "city" : row["c"][2]["v"],
            "month" : row["c"][3]["v"],
            "day" : row["c"][4]["v"],
            "hour" : row["c"][5]["v"],
            "status" : row["c"][6]["v"],
            "comment" : row["c"][7]["v"],
            })
        rows = newrows
        if q:
            newrows = []
            for row in rows:
                if re.search(q,row["pref"] + row["city"]):
                    newrows.append(row)
            newrows = newrows[0:60]

        newrows.reverse()
        return newrows
        
class MainPage(BasePage):
    def get(self):

        q = self.request.get("q")
        format = self.request.get("format")
        
        newrows = getjson(q)
            
        if format == "json":
            test = simplejson.dumps(newrows, ensure_ascii=False)
            self.response.out.write(test)
        else:
            templates = {
            "rows" : newrows
            }
            self.render("../views/top.html",templates)

class TweetPage(BasePage):
    def get(self):

        newrows = getjson("")
        self.response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        
        for row in newrows:
            line = u"【無事情報】"+row["pref"]+u"県"+row["city"]+u"市で、無事が確認されました。http://buji.me #buji [2011/"+ row["month"] + "/" + row["day"] + " "+row["hour"]+u"時頃の情報]\n"
            self.response.out.write(line)     
        
def is_local():
    domain = ''
    if os.environ.has_key("SERVER_NAME"):
        domain = os.environ["SERVER_NAME"]
    isLocal = (not domain or not re.search("(buji\.me|appspot\.com)",domain))
    return isLocal


webapp.template.register_template_library("customtags.xss")
webapp.template.register_template_library("customtags.link")

application = webapp.WSGIApplication([  ('/', MainPage),
                                         ('/tweet', TweetPage),
                                        ],
                                     debug=is_local())

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
