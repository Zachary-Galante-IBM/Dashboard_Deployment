import functools

from flask import session, redirect

from dash import html, dcc

from auth import AppIDAuthProvider

class AppIDAuthProviderDash(AppIDAuthProvider):

    def __init__(self, dash_url):

        super().__init__()

        @self.flask.route("/startauth")
        def startauth():
            session[AppIDAuthProvider.ENDPOINT_CONTEXT] = dash_url
            return AppIDAuthProvider.start_auth()

        @self.flask.route("/")
        def index():
            auth_active, _ = AppIDAuthProvider._is_auth_active()
            if auth_active:
                return redirect(dash_url)
            else:
                return redirect("/startauth")

    @classmethod
    def check(cls, func):
        @functools.wraps(func)
        def wrapper_check(*args, **kwargs):
            auth_active, err_msg = cls._is_auth_active()
            if not auth_active:
                if err_msg:
                    err_msg = "Internal error: " + err_msg
                    return [html.Div(children = err_msg,
                                     style = {"textAlign": "center", "font-size": "20px", "color": "red"})]
                else:
                    return [html.Div(children = [dcc.Link("Log in", href = "/startauth", refresh = True)],
                                     style = {"textAlign": "center", "font-size": "30px"})]
            else:
                if not cls._user_has_a_role():
                    return [html.Div(children = "Unauthorized!",
                                     style = {"textAlign": "center", "font-size": "20px", "color": "red"})]
                else:
                    return func(*args, **kwargs)
        return wrapper_check
