import asyncio
import re
import time
import traceback
from functools import partial
from pathlib import Path
from typing import Any

import jinja2
from flask import render_template_string
from markupsafe import Markup

from flask_orphus.event import Event
from flask_orphus.logging import Log

fire_starter: Event = Event()
log = Log()


def async_partial(f, *args):
    async def f2(*args2):
        result = f(*args, *args2)
        if asyncio.iscoroutinefunction(f):
            result = await result
        return result

    return f2


def micro_render(app, bang_template: Path, **context: dict[Any, Any]) -> str:
    if context is None:
        context = {}
    st: float = time.time()
    fire_starter.fire("template_rendering_began", message=f"Began rendering template [{bang_template}]")
    with open(bang_template, 'r') as bang_f:
        template: str = bang_f.read()
        bang_pattern: str = r'---\n(.*?)\n---'
        bang_result: Any = re.findall(bang_pattern, template, re.DOTALL)
    bang_vals: dict[Any, Any] = {}
    for bang_script in bang_result:
        try:
            exec(bang_script.strip(), locals())
            bang_vals.update(locals())
            # remove all keys from locals that do not start with bang_
            for bang_key in list(bang_vals.keys()):
                if bang_key.startswith("bang_"):
                    del bang_vals[bang_key]

        except Exception as e:
            traceback_str = traceback.format_exc()
            raise e

    if str(bang_template).startswith("components") or str(bang_template).startswith("layouts"):
        style_pattern = r'<style.*?>(.*?)</style>'
        style_result = re.findall(style_pattern, template, re.DOTALL)
        style_result = "\n".join(style_result)

        for style in style_result:
            component_html = template.replace(style, "")
        original_css = style_result
        # TODO: fix this


    stripped_template = re.sub(r"^.*?(<template>.*?</template>).*?$", r"\1", template, flags=re.DOTALL)
    html_str: str = stripped_template.strip().lstrip("<template>").rstrip("</template>")

    if str(bang_template).startswith("components") or str(bang_template).startswith("layouts"):
        html_str = f"<style>{original_css}</style>" + html_str

    if context:
        bang_vals.update(context)
    with app.app_context():
        app.jinja_env.enable_async = True
        app.jinja_env.globals['_render'] = partial(micro_render, app)

        if str(bang_template).startswith("components") or str(bang_template).startswith("layouts"):
            component_html = html_str
            output = Markup(render_template_string(component_html, **bang_vals))
        else:
            try:
                layout_file = bang_vals.get("layout", "Layout.html")
                output_builder_start = f"""{{% extends '{layout_file}' %}}{{% block content %}}"""
                output_builder_end = """{% endblock %}"""
                output_build = output_builder_start + html_str + output_builder_end
                output = render_template_string(output_build, **bang_vals)

            except jinja2.exceptions.TemplateNotFound:
                output: str = render_template_string("""
                        html_str
                """.replace("html_str", html_str), **bang_vals)
        et: float = time.time()
        fire_starter.fire("template_rendering_ended",
                          message=f"Ended rendering [{bang_template}] template took {et - st} seconds")
        return output


@fire_starter.event("template_rendering_began")
def on_template_rendering_began(message: str) -> None:
    log.info(message)
    pass


@fire_starter.event("template_rendering_ended")
def on_template_rendering_ended(message: str) -> None:
    log.info(message)
    pass
