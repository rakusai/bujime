# -*- coding: utf-8 -*-

#pre import
execfile("pre_import.py")


class NewRoomPage(BasePage):
    '''新規ルーム作成'''
    def post(self):
        room = Room.create()
        room.put()

        #Roomにユーザーを追加
        userkey = self.get_userkey()
        room.addmember(userkey)

        self.redirect("/r" + room.keyname())

class RoomPage(BasePage):
    '''ルームページ'''
    def get(self, room_key):
        if not self.basicAuth():
            self.response.out.write("Unauthorized")
            return

        room = Room.get_by_key_name(room_key)
        if not room:
            self.response.out.write("no room")
            return
        room.remain_member_count = 15 - len(room.active_members)

        #chat logs
        chatlogs = ChatLog.all().filter("room_key =",room_key).order("-date").fetch(50)
        chatlogs.reverse()
        
        chatcount = 0
        chatuser = False
        for chatlog in chatlogs:
            chatlog.time = chatlog.date.strftime("%Y/%m/%d %H:%M:%S")
            chatcount = chatcount + 1
            if chatuser == chatlog.username:
                chatlog.nouser = True
            else:
                chatlog.nouser = False
                chatuser = chatlog.username
        
        showlogs = (chatcount >= 50)
        enterlimit = (len(room.active_members) >= 15)
        
        template_values = {
        "page_title" : room.title,
        "room" : room,
        "chatlogs" : chatlogs,
        "showlogs" : showlogs,
        "enterlimit" : enterlimit,
        }
        self.render('../views/room.html',template_values)

class ApiRoomChangeTitle(BasePage):
    '''ルームタイトル変更'''
    def post(self):
        room_key = self.request.get("room_key")
        title = self.request.get("title")

        room = Room.get_by_key_name(room_key)
        if not room:
            self.render_json({"stat":"fail","msg":"no room"})
            return
        
        room.title = title
        room.put()
        self.render_json({"stat":"ok"})

class ApiRoomEnter(BasePage):
    '''API ルーム入室'''
    def post(self):
        room_key = self.request.get("room_key")
        username = self.request.get("username")
        hash = self.request.get("hash") #flash serverのID

        room = Room.get_by_key_name(room_key)
        if not room:
            self.render_json({"stat":"fail","msg":"no room"})
            return
        
        
        #usernameの保存
        userkey = self.get_userkey()
        self.session.set("username",username)
        if self.user:
            person = Person.get_by_key_name(userkey)
            if person:
                person.username = username #表示名を保存
                person.put()
        
        #Roomにユーザーを追加
        room.addmember(userkey)
        
        logging.info("username:" + username + "\nroom:" + room_key + "\nuserkey:" + userkey)

        #第1回目のactiveを呼び出す。
        taskqueue.add(url='/api/room/active', params={"room_key":room_key,"userkey":userkey}, method = 'POST')

        self.render_json({"stat":"ok"})

class ApiRoomLeave(BasePage):
    '''部屋から脱退'''
    def post(self):
        room_key = self.request.get("room_key")
        room = Room.get_by_key_name(room_key)
        if not room:
            self.render_json({"stat":"fail","msg":"no room"})
            return

        userkey = self.get_userkey()
        room.leave_member(userkey)

        self.render_json({"stat":"ok"})
                


class ApiRoomActive(BasePage):
    '''API ルーム滞在ポーリング'''
    def post(self):
        room_key = self.request.get("room_key")
        userkey = self.request.get("userkey") #taskqueから渡される
        
        if not userkey:
            userkey = self.get_userkey()

        cache = memcache.get("active//"+userkey+"/"+room_key)
        if not cache or cache < datetime.now() - timedelta(seconds=60+20):
            #中断されていた
            room = Room.get_by_key_name(room_key)
            if room:
                #Roomにユーザーを追加
                room.addmember(userkey)
            


        #memcacheに保存
        memcache.set("active//"+userkey+"/"+room_key,datetime.now(),60*5)
        
        self.render_json({"stat":"ok"})

        params = {
            "room_key" : room_key,
            "userkey" : userkey,
        }

        #taskqueueで60+20秒後チェック
        taskqueue.add(url='/api/room/leavecheck', params=params, method = 'POST', countdown=60+20)


class ApiRoomLeaveCheck(webapp.RequestHandler):
    '''API ルームブラウザが閉じたか確認'''
    def post(self):
        room_key = self.request.get("room_key")
        userkey = self.request.get("userkey")

        cache = memcache.get("active//"+userkey+"/"+room_key)
        if not cache or cache < datetime.now() - timedelta(seconds=60):
            #閉じた
            logging.info("inactivate room: " + userkey) 
            #Roomからユーザーを削除
            room = Room.get_by_key_name(room_key)
            if room:
                room.inactivate_member(userkey)
        else:
            logging.info("stay room: " + userkey) 
        
        self.response.out.write("ok")

