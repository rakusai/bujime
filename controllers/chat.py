# -*- coding: utf-8 -*-

#pre import
execfile("pre_import.py")



class ApiChatAppendMessage(BasePage):
    def post(self):
        room_key = self.request.get("room_key")
        username = self.request.get("username")
        text = self.request.get("text")

        room = Room.get_by_key_name(room_key)
        if not room:
            self.render_json({"stat":"fail","msg":"no room"})
            return
        
        chat = ChatLog()
        chat.room_key = room_key
        chat.username = username
        chat.text = text
        chat.user = self.user
        chat.put()
        self.render_json({"stat":"ok"})

class ChatPage(BasePage):
    def get(self, room_key):
        if not self.basicAuth():
            self.response.out.write("Unauthorized")
            return

        room = Room.get_by_key_name(room_key)
        if not room:
            self.response.out.write("no room")
            return
        
        page = self.init_pagenation()
        fetch_count = 100
        total_count =  20000
        # total_count = memcache.get("recipe_count")
        # if not total_count:
        #     stat = CustomSearchStat.get_by_key_name("total")
        #     if stat:
        #         total_count = stat.tatal_recipe
        #         # memcache.set("recipe_count", recipe_count)
        #     else:
        #         total_count = 0

        #chat logs
        chatlogs = ChatLog.all().filter("room_key =",room_key).order("-date").fetch(fetch_count,(page-1)*fetch_count)
        chatlogs.reverse()
        pages = self.make_pagenation(page, int(total_count/fetch_count)+1)

        chatuser = False
        for chatlog in chatlogs:
            if chatuser == chatlog.username:
                chatlog.nouser = True
            else:
                chatlog.nouser = False
                chatuser = chatlog.username
        
        template_values = {
        "page_title" : "Chat log",
        "room" : room,
        "chatlogs" : chatlogs,
        "pages" : pages,
        }
        self.render('../views/chat.html',template_values)


