# -*- coding: utf-8 -*-

#pre import
execfile("pre_import.py")



class GoogleLogin(BasePage):
    '''ログイン'''
    def get(self):
        user = users.get_current_user()
        redirect_url = self.request.get('redirect')

        if not redirect_url:
            redirect_url = '/'
        redirect_url = "/google_finish?redirect="+ urllib.quote(redirect_url.encode('utf-8',"ignore"))
#        if user is not None:
#            self.error("すでにログイン済みです。")
#        else:
        self.redirect(users.create_login_url(redirect_url))

class GoogleFinish(BasePage):
    '''Googleログイン完了直後'''
    def get(self):
        redirect_url = self.request.get('redirect')
        
        self.after_google_login()
        #roomデータをすべて引き継ぐ
        self.move_rooms_to_user()

        self.redirect(redirect_url)

class GoogleLogout(BasePage):
    '''ログアウト'''
    def post(self):
        self.get()
        
    def get(self):

        redirect_url = self.request.get('redirect_url',"/")
        client = OAuthClient('twitter', self)
        if client.get_cookie():
            self.logout()
            client.logout("/") 
            return
            
        if self.user is None:
            self.redirect('/')
            #self.error('すでにログアウト済みです') 退会時にここに来るのでエラー出力はしない
            return
        self.logout()
        
#        if self.user.service == 'google':
#            self.redirect(users.create_logout_url('/'))
#        else:
        self.redirect(redirect_url)
            
            
class TwitterFinishHandler(BasePage):
    """Demo Twitter App."""

    def get(self):

        client = OAuthClient('twitter', self)
#        gdata = OAuthClient('google', self, scope='http://www.google.com/calendar/feeds')

        write = self.response.out.write; write(HEADER)

        if not client.get_cookie():
            write('<a href="/oauth/twitter/login">Login via Twitter</a>')
            write(FOOTER)
            return

        write('<a href="/oauth/twitter/logout">Logout from Twitter</a><br /><br />')

        info = client.get('/account/verify_credentials')

        write("<strong>Screen Name:</strong> %s<br />" % info['screen_name'])
        write("<strong>Image:</strong> <img src=%s /><br />" % info['profile_image_url'])
        write("<strong>Name:</strong> %s<br />" % info['name'])
        write(info)
        write("<strong>Location:</strong> %s<br />" % info['location'])

        if info and info['id_str']:
            self.after_twitter_login(info)
            #roomデータをすべて引き継ぐ
            self.move_rooms_to_user()

#        rate_info = client.get('/account/rate_limit_status')
#        write("<strong>API Rate Limit Status:</strong> %r" % rate_info)

        write(FOOTER)

        self.redirect("/")

class FacebookFinishHandler(BasePage):
    '''Facebookログイン完了'''
    def post(self):
        self.get()
    def get(self):
        uid = self.request.get("uid")
        name = self.request.get("name")
        thumbnail_url = self.request.get("pic")
        go_redirect = self.request.get("redirect")

        #facebook
        person = Person.get_or_insert("facebook:"+uid)
        person.service = 'facebook'
        person.facebook_id = uid
        if not person.username:
            person.username = name
        if thumbnail_url:
            person.thumbnail_url = thumbnail_url
#        person.fullname = name
        person.put()
        self.session.set("userkey","facebook:"+uid)
        self.session.set("username",name)
        self.user = person

        #roomデータをすべて引き継ぐ
        self.move_rooms_to_user()
        
        self.render_json({"stat":"ok"})

        if go_redirect == 'true':
            self.redirect("/")
