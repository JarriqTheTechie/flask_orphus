import os
from flask_orphus.http import Session, Redirect
from flask_orphus.routing.fs_router import endpoint


@endpoint(name="logout")
def default():
    Session().flush()
    return Redirect.to(os.getenv("AUTH_LOGOUT_REDIRECT_PATH")).route()

