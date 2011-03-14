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
from django.utils import simplejson


def fetchjson(response,key):
    '''spread sheetからjsonを取得し、pythonオブジェクトに変換'''
    sql = "" #"select * "
    sql = urllib.quote(sql)
#        url = "http://spreadsheets.google.com/tq?key=twenqTTEoUUigkPWhKdHhUA&tq=" + sql
    
    json = None 
    json = memcache.get("cache_json/"+key)
    if json:
        return json #キャッシュを返して終了
    
    url = "http://spreadsheets.google.com/tq?key=" + key
    result = urlfetch.fetch(url)
    res  = result.content
    
#        return
    res = res.replace("google.visualization.Query.setResponse(","")
    res = re.sub("\)\;$","",res)
    res = res.replace("yyyy/MM/dd H:mm:ss","")
    res = res.replace("#0.###############","")
    res = re.sub("('style'\:\'[^\']+\')","",res)
    res = re.sub("new Date\(([\d\,]+)\)","'\\1'",res)
    res = res.replace('c:[,','c:[{v:\'\',f:\'\'},') #google spread sheetのバグ。日付型に文字がはいっているとオブジェクトが出力されない

    res = res.replace("},,{","},{v:''},{") #spread sheetのバグ対応

    res = re.sub("([{,])([a-z]+)\:","\\1'\\2':",res) #変数名をクオーテーションで囲む
    res = re.sub(":([0-9]+)\.[0-9]+",":'\\1'",res) #小数点
    res = res.replace('"','')
    res = res.replace("\\n",' ')
    res = res.replace("},","},\n") #改行をいれてデバッグしやすく
    res = res.replace("'",'"') #ダブルクオーテーションじゃないとパースしてくれない
#    response.out.write(res)
#        return
#        self.response.out.write(res)
#        logging.info(res)
   # res = '{"name": "John Smith", "age": 33}'
    
    try:
        json = simplejson.loads(res)
    except:
        logging.error("simple json parse error!!")
        json = memcache.get("backup/"+key)
    
    if json:
        try:
            memcache.set("backup/"+key,json)
            memcache.set("cache_json/"+key,json,20)
        except:
            logging.error("set memcache error!!")
#        logging.info(json)

    return json

def addlink(str):
    cgi.escape(str)
    # [[ ]] ブロック
    def subblock(m):
        ch = m.group(1) # マッチ・オブジェクトmのgroup(0)は、ヒットした文字列を取り出す。
        lb = ch
        if len(ch) > 50:
            lb = ch[0:50] + "..."
        ch = '<a href="'+ch+'" target="_blank">'+lb+'</a>'
        return ch
        
    block = re.compile(r'(https?:\/\/[a-zA-Z0-9_\.\/\~\%\:\#\?=&\;\-,]+)')
    str = block.sub(subblock,str) 
    str = re.sub("@(\w+)",'<a target="_blank" href="http://twitter.com/\\1">@\\1</a>',str)
    
    return str

def getjson(response,q,page,limit,version,status,link):
        
    key = 'tgjMrXxdYuNdW0JEMBi36bA'
    json = fetchjson(response,key)
    newrows = []
    
    rows = json["table"]["rows"]
    for row in rows:
        comment = row["c"][7]["v"]
        if link == 'yes': 
            comment = addlink(comment)
        
        newrows.append({
        "time" : row["c"][0]["f"],#ここだけf
        "pref" : row["c"][1]["v"],
        "city" : row["c"][2]["v"],
        "month" : row["c"][3]["v"],
        "day" : row["c"][4]["v"],
        "hour" : row["c"][5]["v"],
        "status" : row["c"][6]["v"],
        "comment" : comment,
        })
        
    
    #ここからフィルタリング
    rows = newrows
    if q:
        newrows = []
        for row in rows:
            if re.search(q,row["pref"] + row["city"]):
                newrows.append(row)
    
    rows = newrows
    if status:
        newrows = []
        for row in rows:
            sq = status
            if status == "yes":
                sq = u"確認できました"                    
            elif status == "no":
                sq = u"確認できませんでした"                    

            if re.search(sq,row["status"]):
                newrows.append(row)
    
    newrows.reverse()
    count = len(newrows)
    newrows = newrows[(page-1)*limit:page*limit]

    result = None
    if version == 1:
        result = newrows
    else:            
        result = {"count":count,
                "page" : page,
                "maxpage":int(count/limit)+1,
                "rows":newrows}

    return result
        
class MainPage(BasePage):
    def get(self):
        '''無事.me情報'''
        q = self.request.get("q")
        format = self.request.get("format")
        page = int(self.request.get("page",1)) or 1
        limit = int(self.request.get("limit",60)) or 60
        version = int(self.request.get("ver",1)) or 1
        status = self.request.get("status")
        link = self.request.get("link","")
        
        newrows = getjson(self.response, q, page, limit,version,status,link)
            
        if format == "json":
            self.render_json(newrows)
        else:
            templates = {
            "rows" : newrows
            }
            self.render("../views/top.html",templates)


class GenbaPage(BasePage):
    def get(self):
        '''震災現場情報'''
    
        q = self.request.get("q")
        id = self.request.get("id")
        page = int(self.request.get("page",1)) or 1
        limit = int(self.request.get("limit",60)) or 60

        key = 'tFoqCAAfNuMdwK6_DAeN3CQ'
        json = fetchjson(self.response,key)
        newrows = []
        
        
#        return
        rows = json["table"]["rows"]
        cols = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z","aa","ab","ac","ad","ae","af"]
        newrows = []
        for row in rows:
            newrow = {}
            for x in xrange(len(row["c"])):
                newrow[cols[x]] = row["c"][x]["v"]
            
            newrows.append(newrow)
            
        
        #ここからフィルタリング
        rows = newrows
        if q:
            newrows = []
            for row in rows:
                if re.search(q,row["b"] + row["c"] + row["d"] + row["e"]):
                    newrows.append(row)
        rows = newrows
        if id:
            newrows = []
            for row in rows:
                if id == row["a"]:
                    newrows.append(row)
        
        newrows.reverse()
        count = len(newrows)
        newrows = newrows[(page-1)*limit:page*limit]
    
        result = None
        result = {"count":count,
                "page" : page,
                "maxpage":int(count/limit)+1,
                "rows":newrows}
        self.render_json(result)
    
        
def is_local():
    domain = ''
    if os.environ.has_key("SERVER_NAME"):
        domain = os.environ["SERVER_NAME"]
    isLocal = (not domain or not re.search("(buji\.me|appspot\.com)",domain))
    return isLocal


webapp.template.register_template_library("customtags.xss")
webapp.template.register_template_library("customtags.link")

application = webapp.WSGIApplication([  ('/', MainPage),
                                         ('/genba', GenbaPage),
                                        ],
                                     debug=is_local())

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
