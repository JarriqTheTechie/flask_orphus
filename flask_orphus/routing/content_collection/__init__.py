import pprint
import re
import traceback
from pathlib import Path
from typing import Any

from flask_orphus.helpers import String
from flask_orphus.routing import micro_render


class ContentNotFoundError(Exception):
    pass

class ContentCollection:
    def __init__(self):
        self.name: str | None = None
        self.collection_directory: list[Path] = []

    @classmethod
    def of(self, name: str):
        """
        Instantiate a new String object.
        :param string:
        :return:
        """
        obj = self()
        obj.name = name
        return obj

    def get_collection(self) -> list[Path]:
        pages_path = Path(f'content\\{self.name}')
        pages_html = list(pages_path.glob('**/*.html'))
        [
            self.collection_directory.append(
                page
            )
            for page in pages_html
        ]

        return self

    def grab_html(self, slug: str):
        from app import app as app_cxt
        for page in self.collection_directory:
            if str(String.of(page.stem).kebab()) == str(String.of(slug).kebab()):
                return micro_render(app_cxt, page)
        raise ContentNotFoundError(f"Page with slug [{slug}] not found")

    def collection(self):
        self.get_collection()
        collection_object = []
        for page in self.collection_directory:
            collection_object.append({
                "slug": str(String.of(page.stem).kebab()),
                "html": self.grab_html(str(String.of(page.stem).kebab())),
                "meta": self.grab_meta(page),
            })
        # pprint.pprint(collection_object)
        return collection_object

    def match(self, slug: str):
        self.get_collection()
        for page in self.collection_directory:
            if str(String.of(page.stem).kebab()) == str(String.of(slug).kebab()):
                return {
                    "slug": str(String.of(page.stem).kebab()),
                    "html": self.grab_html(str(String.of(page.stem).kebab())),
                    "meta": self.grab_meta(page),
                }
        raise ContentNotFoundError(f"Page with slug [{slug}] not found")

    def grab_meta(self, page):
        with open(page, 'r') as page_f:
            page_content = page_f.read()
            page_meta = re.findall(r'---\n(.*?)\n---', page_content, re.DOTALL)
            meta = {}
            for meta_script in page_meta:
                try:
                    exec(meta_script.strip())
                    meta.update(locals())
                    # remove all keys from locals that do not start with bang_
                    for meta_key in list(meta.keys()):
                        if meta_key.startswith("meta_"):
                            del meta[meta_key]

                except Exception as e:
                    traceback_str = traceback.format_exc()
                    print(f'ERROR: {traceback_str}')
        return meta



