import logging
from datetime import datetime

import requests

from .form_parser import FormParser

LOGIN_URL = "https://www.eparkai.lt/user/login?destination=/user/{}/generation"
GENERATION_URL = "https://www.eparkai.lt/user/{}/generation?ajax_form=1&_wrapper_format=drupal_ajax"

MONTHS = [
    "Sausio", "Vasario", "Kovo",
    "Balandžio", "Gegužės", "Birželio",
    "Liepos", "Rugpjūčio", "Rugsėjo",
    "Spalio", "Lapkričio", "Gruodžio"
]

_LOGGER = logging.getLogger(__name__)


class EParkaiClient:

    def __init__(self, username: str, password: str, client_id: str):
        self.username: str = username
        self.password: str = password
        self.client_id: str = client_id
        self.session: requests.Session = requests.Session()
        self.cookies: dict | None = None
        self.form_parser: FormParser = FormParser()
        self.generation: dict = {}

    def login(self) -> None:
        self.generation = {}

        response = self.session.post(
            LOGIN_URL.format(self.client_id),
            data={
                "name": self.username,
                "pass": self.password,
                "login_type": 1,
                "form_id": "user_login_form"
            },
            allow_redirects=True
        )

        response.raise_for_status()

        _LOGGER.debug(f"Got login response: {response.text}")

        self.cookies = requests.utils.dict_from_cookiejar(response.cookies)

        self.form_parser.feed(response.text)

    def fetch(self, power_plant_id: str, object_address: str | None, date: datetime) -> dict:
        if self.form_parser.get("form_id") != "product_generation_form":
            raise Exception("Form ID not found. Check your credentials OR login to eparkai.lt and confirm contact information.")

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",            
        }

        response = self.session.post(
            GENERATION_URL.format(self.client_id),
            data={
                "address": object_address,
                "period": "week",
                "current_date": date.strftime("%Y-%m-%d"),
                "generation_electricity": power_plant_id,
                "form_build_id": self.form_parser.get("form_build_id"),
                "form_token": self.form_parser.get("form_token"),
                "form_id": self.form_parser.get("form_id"),
                "_drupal_ajax": "1",
                "_triggering_element_name": "period",
            },
            headers=headers,
            cookies=self.cookies,
            allow_redirects=False
        )

        response.raise_for_status()

        _LOGGER.debug(f"Got fetch response: {response.text}")

        return response.json()

    def fetch_generation_data(self, power_plant_id: str, object_address: str, date: datetime) -> None:
        if power_plant_id in self.generation:
            return

        self.generation[power_plant_id] = {}

        data = self.fetch(power_plant_id, object_address, date)

        for d in data:
            if d["command"] != "settings":
                continue

            if "product_generation_form" not in d["settings"] or not d["settings"]["product_generation_form"]:
                continue

            generation = d["settings"]["product_generation_form"]

            for idx, value in enumerate(generation["data"]):
                if value is None:
                    value = 0

                date = self.parse_date(" ".join(generation["labels"][idx]))
                ts = int(datetime.timestamp(datetime.strptime(date, "%Y %m %d %H:%M")))

                self.generation[power_plant_id][ts] = float(value)

    def get_generation_data(self, power_plant_id: str) -> dict | None:
        if power_plant_id not in self.generation:
            return None

        return self.generation[power_plant_id]

    @staticmethod
    def parse_date(date: str) -> str:
        [year, month, day, time] = date.split(" ")

        month = str(MONTHS.index(month.replace("Rugsėo", "Rugsėjo")) + 1)

        return " ".join([year, month.zfill(2), day, time])
