import os
import subprocess
import shutil
from typing import Literal

import click
import inflection
from flask import request
from jinja2 import FileSystemLoader

from flask_orphus.helpers import String
from flask_orphus.http import Request, Redirect
from flask_orphus.logging import Log
from flask_orphus.routing.content_collection import ContentNotFoundError
from flask_orphus.routing.fs_router import FSRouter
from flask_orphus.routing.fs_router_api import FSRouterAPI
from flask_orphus.validation import ValidationError
from dotenv import load_dotenv

routing_modes = Literal[
    "pages",
    "api",
    "hybrid"
]

load_dotenv()


class FlaskOrphus:
    def __init__(self, app=None, routing_mode: routing_modes = "pages"):
        self.routing_mode = routing_mode
        if app is not None:
            self.app = app
            app.secret_key = os.getenv("APP_SECRET_KEY")

            app.add_template_global(Request.session, name="session")
            app.add_template_global(Request.session().old, name="old")
            app.add_template_global(Request.session().errors, name="errors")
            app.add_template_global(String, name="String")
            app.add_template_global(os.getenv, name="env")
            match routing_mode:
                case "hybrid":
                    FSRouter(app)
                    FSRouterAPI(app)
                case "api":
                    FSRouterAPI(app)
                case _:
                    FSRouter(app)

            self.init_app(self.app)

    def init_app(self, app):
        app.jinja_env.enable_async = True
        match self.routing_mode:
            case "api":
                app.jinja_env.loader = FileSystemLoader([
                    "pages/api"
                ])
            case "hybrid":
                app.jinja_env.loader = FileSystemLoader([
                    "components",
                    "layouts",
                    "pages",
                    "pages/api"
                ])
            case _:
                app.jinja_env.loader = FileSystemLoader([
                    "components",
                    "layouts",
                    "pages"
                ])

        @app.errorhandler(ValidationError)
        def validationError(e):
            if request.headers.get('Content-Type') == 'application/json':
                print("json")
                return {"errors": ""}
            return Redirect.to().back()

        @app.errorhandler(ContentNotFoundError)
        def contentNotFoundError(e):
            raise e

        @app.cli.command("new-project")
        def new_project():
            import inspect
            stubs_dir = os.path.join(os.path.dirname(inspect.getfile(inspect.currentframe())), "stubs")
            dirs_to_create = [
                "components", "layouts", "pages", "databases/migrations", "databases/seeds",
                "lib/events", "lib/exceptions", "lib/jobs", "lib/mail", "lib/models",
                "lib/notifications", "lib/observers", "lib/repositories", "lib/services",
                "pages/auth"
            ]
            for folder in dirs_to_create:
                try:
                    print(f"Creating Directory {folder}")
                    os.makedirs(f"{folder}")
                except FileExistsError:
                    print(f"Directory {folder} already exists. ")

            try:
                print(f"Creating File requirements.txt")
                with open("requirements.txt", "x") as f:
                    requirements = open(stubs_dir + "/requirements.txt", "r")
                    f.write(
                        requirements.read()
                    )
            except FileExistsError:
                print(f"File Already Exisits - requirements.txt")

            print(f"Creating File .env")
            try:
                with open(".env", "x") as f:
                    env = open(stubs_dir + "/.env", "r")
                    f.write(env.read())
                print("Successfully created new Orphus Project.")
            except FileExistsError:
                print(f"File Already Exisits - .env")

            print(f"Creating File pages/auth/logout.py")
            try:
                with open("pages/auth/logout.py", "x") as f:
                    logout = open(stubs_dir + "/logout.py", "r")
                    f.write(logout.read())
                print("Successfully created new Orphus Project.")
            except FileExistsError:
                print(f"File Already Exisits - pages/auth/logout.py")

        @app.cli.command("make:model")
        @click.argument("model")
        def create_model(model):
            """Creates a model|migration|seeder file."""
            result = subprocess.run([
                "masonite-orm", "model", f'{model}',
                "--migration",
                "--seeder",
                "--create",
                "--directory", "lib/models",
            ], capture_output=True, text=True)
            print(result.stdout)

        @app.cli.command("make:table")
        @click.argument("table_name")
        def create_table(table_name):
            """Creates a migration file for a table."""
            table_name = inflection.pluralize(table_name)
            result = subprocess.run([
                "masonite-orm", "migration", f'create_table_{table_name}',
                "--create", f"{table_name}",
            ], capture_output=True, text=True)
            print(result.stdout)
