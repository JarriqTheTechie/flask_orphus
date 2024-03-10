import importlib
import inspect
import re
import secrets
from functools import wraps, partial
from pathlib import Path
from pydoc import locate
from typing import Any

from werkzeug.routing import BaseConverter

try:
    from config.database import RouteModelBinding
except ImportError:
    pass
from flask_orphus.helpers import String
from flask_orphus.routing.micro import micro_render


class ModelConverter(BaseConverter):
    def __init__(self, url_map, model):
        super().__init__(url_map)
        self.model = model

    def to_python(self, value):
        model = RouteModelBinding.get(self.model)
        primary_key = model.__dict__.get("__primary_key__", "id")
        key = model.__dict__.get(
            "get_route_key_name",
            model.__dict__.get("__route_model_binding_key__")
        )

        if key:
            if callable(key):
                key = getattr(model(), "get_route_key_name")()
                if model.__dict__.get("resolve_route_binding"):
                    return getattr(model(), "resolve_route_binding")(key, value)
            return model.where(key, value).first()
        else:
            return model.find_or_404(value)
        raise Exception(f"Model {self.model} not found in route model binding configuration.")

    def to_url(self, value):
        try:
            if "get_route_key_name" in value.__class__.__dict__.keys():
                key = value.get_route_key_name()
            else:
                key = value.__route_model_binding_key__
        except AttributeError as e:
            if "QueryBuilder" in str(e):
                raise TypeError(
                    f"{value} should be a [Model] and not a [QueryBuilder]. [QueryBuilder] has no attribute [__route_model_binding_key__]. ")
        return str(value[key])


def to_class(path: str) -> Any:
    """
        Converts string class path to a python class

    return:
        mixed
    """
    try:
        class_instance = locate(path)
    except ImportError:
        class_instance = None
    return class_instance or None


def path_processor(path):
    path = path.replace("pages.", "/").replace(".", "/").replace("index/", "").replace(
        "[", "<").replace("]", ">").replace("/index", "").replace("~", "/")

    ["/" if path.rstrip(f"{path.split('.')[-1]}").rstrip("/") == "" else path.rstrip(
        f"{path.split('.')[-1]}").rstrip("/")][0].rstrip(".").replace("/.", "/")

    try:
        from config.database import RouteModelBinding
        pattern = r'<(.*?)>'
        matches = re.findall(pattern, path)
        for match in matches:
            print(match)
            if match in RouteModelBinding.keys():
                path = path.replace(f"<{match}>", f"<model({match}):{match.lower()}>")
    except ImportError:
        pass
    # print(path)
    return path


def get_endpoint_func_post(my_module_str):
    my_module = importlib.import_module(my_module_str)
    my_module_functions = [f for f in vars(my_module).values() if inspect.isfunction(f)]
    for fn in my_module_functions:
        if hasattr(fn, "__is_endpoint__"):
            return f"{my_module_str}.{fn.__name__}"


def get_endpoint_from_get(file_path: str):
    with open(file_path, "r") as f:
        sample = f.read()
    pattern = r"endpoint\s*=\s*(.+?)(?=\n|$)"

    match = re.search(pattern, sample)

    if match:
        endpoint_name = match.group(1).strip()
        return endpoint_name.strip('"')
    else:
        return secrets.token_urlsafe(4)


class FSRouter:
    def __init__(self, app=None):
        self.possible_routes = []
        self.fqdns = []
        self.route_paths = []
        self.route_map = []
        if app is not None:
            self.app = app
            self.init_app(self.app)

    def init_app(self, app):
        try:
            from config.database import RouteModelBinding
            app.url_map.converters['model'] = ModelConverter
        except ImportError:
            pass

        app.jinja_env.enable_async = True

        for route in FSRouter().routes_export():
            page = Path(route.get('file_path'))
            path = path_processor(route.get("path"))

            if path == "/" or path == "":
                path = "/"
            else:
                if path.startswith("/"):
                    if "<" not in path:
                        path = path.lstrip("/")

                        path = str(String.of(path).kebab())
                        path = f"/{path}"

            match route.get("method").upper():
                case "POST" | "DELETE" | "PATCH":
                    file_path = route.get("file_path").replace("\\", ".").rstrip(".py")
                    if path == "":
                        path = "/"
                    app.add_url_rule(
                        path,
                        **dict(
                            view_func=to_class(get_endpoint_func_post(file_path)),
                            endpoint=to_class(get_endpoint_func_post(file_path)).__endpoint_name__,
                            methods=[route.get('method')],
                            websocket=route.get("ws")
                        )
                    )

                case "GET":
                    app.add_url_rule(
                        path,
                        **dict(
                            view_func=[
                                partial(micro_render, app, page)
                                if route.get("file_path").endswith(".html")
                                else
                                to_class(
                                    get_endpoint_func_post(
                                        route.get("file_path").replace("\\", ".").rstrip(".py")
                                    )
                                )
                            ][0],
                            endpoint=[
                                get_endpoint_from_get(route.get("file_path"))
                                if route.get("file_path").endswith(".html")
                                else
                                to_class(
                                    get_endpoint_func_post(
                                        route.get("file_path").replace("\\", ".").rstrip(".py")
                                    )
                                ).__endpoint_name__
                            ][0],
                            methods=[route.get('method')],
                            websocket=route.get("ws")
                        )
                    )

                case _:
                    continue

    def find_routes_files(self):
        pages_path = Path('pages')
        pages_html = list(pages_path.glob('**/*.html'))
        [
            self.possible_routes.append(
                page
            )
            for page in pages_html
        ]
        pages_py = list(pages_path.glob('**/*.py'))
        [
            self.possible_routes.append(
                page
            )
            for page in pages_py
        ]
        return self

    def generate_fqdns(self):
        for my_module in self.possible_routes:
            my_module_str = f"pages.{Path(my_module)}"
            self.fqdns.append(f"{my_module_str}")
        return self

    def fqdns_to_route_path(self):
        for path in self.fqdns:
            file_path = path.replace("pages.", "")
            fqdn = path
            path = path.replace("pages.", "/").replace(".", "/").replace("index/", "").replace(
                "[", "<").replace("]", ">").replace("/index", "").replace("~", "/")

            split_path = path.split(">")
            end_of_arg_position = path.split(">")[0].__len__()
            try:
                if path[end_of_arg_position + 1] != "/":
                    path = f"{path[:end_of_arg_position]}>/{split_path[1]}"
            except IndexError:
                pass

            method = fqdn.split("(")[-1].split(')')[0]
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                method = method
            else:
                method = "GET"

            if path == "/":
                pass
            else:
                path = path.rstrip("/")

            fqdn = fqdn.replace("//", '').replace("/", '.').replace("..", '.').replace("\\", ".")
            path = path.replace("//", '').replace("..", '.').replace("\\", ".")
            path = path.replace("/pages", '/')
            path = path.replace(f'({method})', '').replace("//", '/') or '/'

            self.route_map.append({
                "path": ["/" if path.rstrip(f"{fqdn.split('.')[-1]}").rstrip("/") == "" else path.rstrip(
                    f"{fqdn.split('.')[-1]}").rstrip("/")][0].rstrip(".").replace("/.", "/"),
                "fqdn": fqdn,
                # "view_func": micro_render(file_path),
                "endpoint": secrets.token_urlsafe(4),
                "method": method,
                "ws": to_class(fqdn.replace(f"{fqdn.split('.')[-1]}", "ws")) or False,
                "file_path": file_path
            })
        return self

    def routes_export(self):
        return self.find_routes_files().generate_fqdns().fqdns_to_route_path().route_map


def endpoint(func_=None, name: str = ""):
    def _decorator(func):
        func.__is_endpoint__ = True
        func.__endpoint_name__ = name

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    if callable(func_):
        return _decorator(func_)
    elif func_ is None:
        return _decorator
    else:
        raise ValueError("Positional arguments are not supported.")
