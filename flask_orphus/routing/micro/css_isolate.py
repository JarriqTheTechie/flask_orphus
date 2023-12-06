import pprint
import re

from bs4 import BeautifulSoup


def includes(str: str, sub: str):
    if str.find(sub) < 0:
        return False
    else:
        return True


def unique(sequence):
    result = []
    for item in sequence:
        if item not in result:
            result.append(item)
    return result


def css_isolate(css: str, html: str, is_style: bool = False, class_name: str = ""):
    css = css.replace("\n", "").replace("  ", "").replace("}", "}")
    replacement_pairs = []

    expr = re.compile(r'(.*?)\{.*?\}')

    for res in expr.findall(css):
        for tag in res.split():
            tag = tag.strip(",")
            if tag != "~" and tag != "+" and tag != ">":
                replacement_pairs.append({
                    f"{tag}": (
                        f'{tag}[data-hubi="{class_name}"]', f'data-hubi="{class_name}"'
                    )
                })

    for style in list(set(css.splitlines())):
        style = style.split("{")[0].lstrip().rstrip().strip(" ")
        if " " not in style:
            replacement_pairs.append({
                f"{style}": (
                    f'{style}[data-hubi="{class_name}"]', f'data-hubi="{class_name}"'
                )
            })
        else:
            paired_styles = style.strip(" ").split(" ")
            for paired_style in paired_styles:
                if "," not in paired_style or ">" not in paired_style:
                    replacement_pairs.append({
                        f"{paired_style}": (
                            f'{paired_style}[data-hubi="{class_name}"]', f'data-hubi="{class_name}"'
                        )
                    })
                if "," in paired_style:
                    replacement_pairs.append({
                        f"{paired_style}": (
                            f'{paired_style.strip(",")}[data-hubi="{class_name}"],', f'data-hubi="{class_name}"'
                        )
                    })
                if ">" in paired_style:
                    replacement_pairs.append({
                        f"{paired_style}": (
                            f'{paired_style.strip(">")}[data-hubi="{class_name}"] >', f'data-hubi="{class_name}"'
                        )
                    })

    replacement_tags = []

    for d in unique(replacement_pairs):
        replacement_key = list(d.keys())[0]
        if replacement_key not in [">", ","]:
            if is_style:
                if f"{replacement_key}" in html:
                    html = html.replace(
                        f"{replacement_key}",
                        f"{d[f'{replacement_key}'][0]}"
                    )

            else:
                soup = BeautifulSoup(html, 'html.parser')
                matches = soup.select(f"{replacement_key.strip(',').split(':')[0]}")
                for match in matches:
                    val: str = str(match)
                    index = val.index(" ")
                    replacement = val[:index] + f' {list(d.values())[0][1]}'
                    replacement_tags.append((
                        str(val[:index]), replacement
                    ))

            if len(replacement_tags) != 0:
                for replacement_tag in replacement_tags:
                    html = html.replace(replacement_tag[0].lstrip().rstrip(), replacement_tag[1].lstrip().rstrip())

    return html
