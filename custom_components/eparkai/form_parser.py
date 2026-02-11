import logging
from html.parser import HTMLParser

_LOGGER = logging.getLogger(__name__)

class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.form: dict = {}

    def handle_starttag(self, tag: str, attrs: tuple) -> None:
        if tag not in ["input", "select"]:
            return
        if tag == "input":
            self.handle_input_tag(attrs)
        elif tag == "select":
            self.handle_select_tag(attrs)

    def get(self, attribute: str) -> str | None:
        return self.form.get(attribute, None)

    def set(self, attribute: str, value: str) -> None:
        self.form[attribute] = value

    def handle_input_tag(self, attrs: tuple) -> None:
        attributes = dict(attrs)
        if "name" in attributes and attributes["name"] in ["form_token", "form_build_id", "form_id"]:
            _LOGGER.debug(f"Found required form attribute: {attributes['name']} = {attributes.get('value', '')}")
            self.form[attributes["name"]] = attributes.get("value", "")

    def handle_select_tag(self, attrs: tuple):
        # TODO: Optionally: parse <select> tag for available power plant ids
        pass
