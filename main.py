import os.path
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import json
from tornado.websocket import WebSocketHandler

import db

# import and define tornado-y things
from tornado.options import define, options
define("port", default=5000, help="run on the given port", type=int)

#NGパスワード
str_ng_password = 'kjhd86z43lk'

# application settings and handle mapping info
class Application(tornado.web.Application):
    def __init__(self):
        # url dispacher
        handlers = [
            (r'/', MainHandler),
            (r'/adduser', AddUserHandler),
            (r'/del_user', DelUserHandler),
            (r'/del_user_commit', DelUserCommitHandler),
            (r'/chg_pass', ChangePassHandler),
            (r'/auth/login', AuthLoginHandler),
            (r'/auth/logout', AuthLogoutHandler),
            (r"/chat", ChatHandler),
        ]

        # setting
        settings = dict(
            cookie_secret='iz67y9d2osbcj0i4mpkspjd9vn9ku88j',
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            login_url="/auth/login",
            xsrf_cookies=False,
            autoescape="xhtml_escape",
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # database initilize
        self.db = db.connect()
        self.db_cur = db.get_dict_cursor(self.db)

# base handlers
class BaseHandler(tornado.web.RequestHandler):

    cookie_username = "username"

    def get_current_user(self):
        username = self.get_secure_cookie(self.cookie_username)
        if not username: return None
        return tornado.escape.utf8(username)

    def set_current_user(self, username):
        self.set_secure_cookie(self.cookie_username, tornado.escape.utf8(username))

    def clear_current_user(self):
        self.clear_cookie(self.cookie_username)

    # データベースのインターフェースを取得する
    @property
    def db(self):
        conn = self.application.db
        return conn

    # データベースのカーソルを取得する
    @property
    def db_cur(self):
        conn = self.application.db_cur
        return conn

    # ナビゲーションのログイン情報HTMLを作成する
    def get_login_html(self):
        if self.get_current_user():
            html = '<div class=\"pull-right\"><font color="#dcdcdc">ユーザー名:' + self.get_current_user().decode('utf-8') + '</font><br><a href="./auth/logout" style="color: #FFFFFF;">ログアウト</a></div>'
            return html
        else:
            # ログイン領域の非ログイン文字列
            html = '<ul class="nav navbar-nav navbar-right"><li class="dropdown">' \
                    '<a href="#" class="dropdown-toggle" data-toggle="dropdown">ログイン<b class="caret"></b></a>' \
                    '<ul class="dropdown-menu"><li><form  class="navbar-form" method="post" action="./auth/login">'
            html = html + self.xsrf_form_html()
            html_end = '<input type="hidden" name="destination" value="http://milk-tea.myvnc.com/bashopita/rssreader.cgi?rm=top_page" />' \
                    '<input type="hidden" name="rm" value="fail_login" /><div class="form-group">' \
                    '<input id="authen_loginfield" name="authen_username" class="form-control" type="text" value="" placeholder="ユーザー名"/>' \
                    '</div><div class="form-group"><input id="authen_passwordfield" name="authen_password" class="form-control" type="password" value="" placeholder="パスワード"/>' \
                    '</div><button id="authen_loginbutton" tabindex="4" type="submit" name="authen_loginbutton" class="btn btn-default">ログイン</button>' \
                    '</form></li><li class="divider"></li><li>' \
                    '<a href="./adduser">ユーザー登録はこちら&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</a>' \
                    '</li></ul></li></ul>'
            return html + html_end

# the main page
class MainHandler(BaseHandler):
    def get(self):
        if not self.get_current_user():
            self.render(
                "top.html",
                navbar_login=self.get_login_html(),
                locale = self.locale.code
                )
        else:
            self.render(
                "user_page.html",
                navbar_login=self.get_login_html()
                )

class AddUserHandler(BaseHandler):
    def get(self):
        self.render(
            "adduser_page.html",
            navbar_login=self.get_login_html()
        )
    def post(self):
        #ポストされたデータを取得する
        szTxtID = self.get_argument("txtID");
        szTxtMail = self.get_argument("txtMail");
        szPass1 = self.get_argument("pass_in");
        szPass2 = self.get_argument("pass_check");

        #エラー処理
        if szTxtID=="":
            #ユーザーIDが未入力
            self.render(
                "adduserresult_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = 'ユーザーIDが設定されていません。<br>ユーザーIDを入力してください。'
            )
            return

        if szPass1=="":
            #パスワードが未入力
            self.render(
                "adduserresult_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = 'パスワードが設定されていません。<br>パスワードを入力してください。'
            )
            return

        if szTxtMail=="":
            #e-mailがあるかを確認する
            self.render(
                "adduserresult_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = 'メールアドレスが設定されていません。<br>メールアドレスを入力してください。'
            )
            return

        if szPass1 == str_ng_password:
            self.render(
                "adduserresult_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = '入力したパスワードは使えません。別の文字列を使用してください。'
            )
            return

        if szPass1 != szPass2:
            self.render(
                "adduserresult_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = 'パスワードが一致しません。<br>再確認してください。'
            )
            return

        #同じユーザーがあるかを確認する
        sqlcmd = 'select * from users where userid=\'' + szTxtID +'\' limit 1'
        self.db_cur.execute(sqlcmd, ())
        result = self.db_cur.fetchone()

        if result != None:
            self.render(
                "adduserresult_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = '指定されたユーザーIDは使用できません。<br>別のユーザーIDを使用して再登録してください。'
            )
            return

        # データを追加する
        try:
            sqlcmd = 'INSERT INTO users(userid, password, mail) VALUES(%s, %s, %s);'
            self.db_cur.execute(sqlcmd, (szTxtID, szPass1, szTxtMail))
            self.db.commit()
        except:
            self.render(
                "adduserresult_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = 'データ追加中にエラーが発生しました。'
            )
            return

        self.render(
            "adduserresult_page.html",
            navbar_login=self.get_login_html(),
            str_result_abstract = '<div class="alert alert-success" role="alert">ユーザー登録完了</div>',
            str_result = 'ユーザーの登録が完了しました。<br>トップページからログインして下さい。'
        )


class DelUserHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render(
            "del_user_confirm.html",
            navbar_login=self.get_login_html()
        )

class DelUserCommitHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        #ユーザーを削除する(なりすまし防止のためパスワードを適当に変更する)
        sqlcmd = 'UPDATE users SET password=\'' + str_ng_password + '\' WHERE userid=\'' + self.get_current_user().decode('utf-8') + '\'';
        self.db_cur.execute(sqlcmd, ())
        self.db.commit()

        #ログアウトする
        self.clear_current_user()
        #結果を表示する
        self.render(
            "del_user_comite.html",
            navbar_login=self.get_login_html()
        )

class ChangePassHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.redirect("/")

    @tornado.web.authenticated
    def post(self):
        #ポストされたデータを取得する
        szPass1 = self.get_argument("pass_in");
        szPass2 = self.get_argument("pass_check");

        #パスワードがあるかを確認する
        if szPass1 == "" :
            self.render(
                "passchange_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = 'パスワードが設定されていません。<br>パスワードを入力してください。'
            )
            return

        if szPass1 == str_ng_password:
            self.render(
                "passchange_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = '入力したパスワードは使えません。別の文字列を使用してください。'
            )
            return

        #パスワードが一致しているかを確認する
        if szPass1 != szPass2 :
            self.render(
                "passchange_page.html",
                navbar_login=self.get_login_html(),
                str_result_abstract = '<div class="alert alert-danger" role="alert">登録エラー</div>',
                str_result = 'パスワードが一致しません。<br>再確認してください。'
            )
            return

        #self.check_xsrf_cookie()

        #パスワードを更新する
        sqlcmd = 'UPDATE users SET password=\'' + szPass1 + '\' WHERE userid=\'' + self.get_current_user().decode('utf-8') + '\'';
        self.db_cur.execute(sqlcmd, ())
        self.db.commit()

        self.render(
            "passchange_page.html",
            navbar_login=self.get_login_html(),
            str_result_abstract = '<div class="alert alert-success" role="alert">変更完了</div>',
            str_result = ''
        )

# login page
class AuthLoginHandler(BaseHandler):

    def get(self):
        self.render(
            "login_page.html",
            navbar_login=self.get_login_html(),
            message=""
        )

    def post(self):
        #self.check_xsrf_cookie()

        username = self.get_argument("authen_username")
        password = self.get_argument("authen_password")

        # 登録したユーザーを検索する
        sqlcmd = 'SELECT * from users where userid=\'' + username +'\''
        self.db_cur.execute(sqlcmd, ())
        result = self.db_cur.fetchone()

        if str_ng_password == password:
        	result = None

        # ユーザーが登録されていないときの処理
        if result == None:
            self.render(
                "login_page.html",
                navbar_login=self.get_login_html(),
                message='<div class="alert alert-danger" role="alert">ユーザーID、または、パスワードが間違っています。</div>'
            )
            return

        if password == result["password"] :
            self.set_current_user(username)
            self.redirect("/")
        else:
            #self.redirect("/auth/login")
            self.render(
                "login_page.html",
                navbar_login=self.get_login_html(),
                message='<div class="alert alert-danger" role="alert">ユーザーID、または、パスワードが間違っています。</div>'
            )

#logout page
class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_current_user()
        self.redirect('/')

# chat function
connections = []

class ChatHandler(BaseHandler, WebSocketHandler):
    @tornado.web.authenticated
    def open(self):
        if self not in connections:
            connections.append(self)

    @tornado.web.authenticated
    def on_message(self, msg):
        parsed_msg = json.loads(msg)
        for conn in connections:
            try:
                if parsed_msg["To"] ==  "all" or parsed_msg["To"] == conn.get_current_user().decode('utf-8'):
                    conn.write_message(msg)
            except:
                connections.remove(conn)

    @tornado.web.authenticated
    def on_close(self):
        if self in connections:
            connections.remove(self)

# main function
def main():
    options.parse_command_line()

    app = Application()
    app.listen(options.port)

    #set traslation dictionary directory
    tornado.locale.load_translations(os.path.join(os.path.dirname(__file__), "translations"))

    # start it up
    tornado.ioloop.IOLoop.instance().start()

# main loop
if __name__ == "__main__":
    main()
