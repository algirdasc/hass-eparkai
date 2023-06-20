import logging
import requests

from datetime import datetime
from typing import Optional

from .form_parser import FormParser

LOGIN_URL = 'https://www.eparkai.lt/user/login?destination=/user/{}/generation'
GENERATION_URL = 'https://www.eparkai.lt/user/{}/generation?ajax_form=1&_wrapper_format=drupal_ajax'

_LOGGER = logging.getLogger(__name__)


class EParkaiClient:

    def __init__(self, username: str, password: str, client_id: str):
        self.username: str = username
        self.password: str = password
        self.client_id: str = client_id
        self.session: requests.Session = requests.Session()
        self.cookies: Optional[dict] = None
        self.form_parser: FormParser = FormParser()
        self.generation: dict = {}

    def login(self) -> None:
        response = self.session.post(
            LOGIN_URL.format(self.client_id),
            data={
                'name': self.username,
                'pass': self.password,
                'login_type': 1,
                'form_id': 'user_login_form'
            },
            allow_redirects=True
        )

        response.raise_for_status()

        if len(response.cookies) == 0:
            _LOGGER.error('Failed to get cookies after login. Possible invalid credentials')
            return

        self.cookies = requests.utils.dict_from_cookiejar(response.cookies)

        self.form_parser.feed(response.text)

    def fetch(self, generation_id: str, date: datetime) -> dict:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
        }

        response = self.session.post(
            GENERATION_URL.format(self.client_id),
            data={
                'period': 'day',
                'current_date': date.strftime('%Y-%m-%d'),
                'generation_electricity': generation_id,
                'form_build_id': self.form_parser.get('form_build_id'),
                'form_token': self.form_parser.get('form_token'),
                'form_id': self.form_parser.get('form_id'),
                '_drupal_ajax': '1',
                '_triggering_element_name': 'period',
            },
            headers=headers,
            cookies=self.cookies,
            allow_redirects=False
        )

        response.raise_for_status()

        return response.json()

    def update_generation(self, generation_id: str, date: datetime) -> None:
        data = self.fetch(generation_id, date)

        for d in data:
            if d['command'] != 'settings':
                continue

            if 'product_generation_form' not in d['settings'] or not d['settings']['product_generation_form']:
                continue

            data = d['settings']['product_generation_form']['data']

            self.generation[generation_id] = [i for i in data if i is not None]

    def get_latest_generation(self, generation_id: str) -> Optional[float]:
        if generation_id not in self.generation:
            return None

        return self.generation[generation_id][-1]
