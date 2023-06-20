from html.parser import HTMLParser
from typing import Optional


class FormParser(HTMLParser):
    form: dict = {}

    def handle_starttag(self, tag: str, attrs: tuple) -> None:
        if tag not in ['input', 'select']:
            return

        if tag == 'input':
            self.handle_input_tag(attrs)
        elif tag == 'select':
            self.handle_select_tag()

    def get(self, attribute: str) -> Optional[dict]:
        if attribute not in self.form:
            return None

        return self.form[attribute]

    def handle_input_tag(self, attrs: tuple) -> None:
        attributes = dict(attrs)
        if 'name' in attributes and attributes['name'] in ['form_token', 'form_build_id', 'form_id']:
            self.form[attributes['name']] = attributes['value']

    def handle_select_tag(self):
        pass
