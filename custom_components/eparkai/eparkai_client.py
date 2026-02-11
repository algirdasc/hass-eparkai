import logging
from datetime import datetime

from aiohttp import ClientError, ClientSession

from .form_parser import FormParser

LOGIN_URL = "https://www.eparkai.lt/user/login?destination=/user/{}/generation"
GENERATION_URL = "https://www.eparkai.lt/user/{}/generation?ajax_form=1&_wrapper_format=drupal_ajax"

MONTHS = [
    "Sausio",
    "Vasario",
    "Kovo",
    "Balandžio",
    "Gegužės",
    "Birželio",
    "Liepos",
    "Rugpjūčio",
    "Rugsėjo",
    "Spalio",
    "Lapkričio",
    "Gruodžio",
]

_LOGGER = logging.getLogger(__name__)


class EParkaiClient:
    def __init__(self, session: ClientSession, username: str, password: str, client_id: str):
        self.username = username
        self.password = password
        self.client_id = client_id
        self.session = session
        self.form_parser = FormParser()
        self.generation: dict[str, dict[int, float]] = {}

    async def login(self) -> None:
        """Login and capture required form fields for subsequent AJAX fetch."""
        self.generation = {}
        try:
            async with self.session.post(
                LOGIN_URL.format(self.client_id),
                data={
                    "name": self.username,
                    "pass": self.password,
                    "login_type": 1,
                    "form_id": "user_login_form",
                },
                allow_redirects=True,
            ) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except ClientError as e:
            _LOGGER.error("eParkai login error: %s", e)
            raise

        _LOGGER.debug("Got login response (len=%s)", len(text))
        self.form_parser.feed(text)

    async def fetch(self, power_plant_id: str, object_address: str | None, date: datetime) -> list[dict]:
        if self.form_parser.get("form_id") != "product_generation_form":
            raise RuntimeError(
                "Form ID not found. Check your credentials OR login to eparkai.lt and confirm contact information."
            )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest",
        }

        try:
            async with self.session.post(
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
                allow_redirects=False,
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except ClientError as e:
            _LOGGER.error("eParkai fetch error: %s", e)
            raise

        return data

    async def fetch_generation_data(self, power_plant_id: str, object_address: str | None, date: datetime) -> None:
        if power_plant_id in self.generation:
            return

        self.generation[power_plant_id] = {}
        data = await self.fetch(power_plant_id, object_address, date)

        for d in data:
            if d.get("command") != "settings":
                continue

            settings = d.get("settings") or {}
            generation = settings.get("product_generation_form")
            if not generation:
                continue

            labels = generation.get("labels") or []
            values = generation.get("data") or []

            for idx, value in enumerate(values):
                if value is None:
                    value = 0

                try:
                    date_str = " ".join(labels[idx])
                    parsed = self.parse_date(date_str)
                    ts = int(datetime.timestamp(datetime.strptime(parsed, "%Y %m %d %H:%M")))
                    self.generation[power_plant_id][ts] = float(value)
                except Exception as e:
                    _LOGGER.error("Failed to parse generation row idx=%s (%s): %s", idx, labels[idx] if idx < len(labels) else None, e)

    def get_generation_data(self, power_plant_id: str) -> dict[int, float] | None:
        return self.generation.get(power_plant_id)

    @staticmethod
    def parse_date(date: str) -> str:
        year, month, day, time = date.split(" ")
        month = str(MONTHS.index(month.replace("Rugsėo", "Rugsėjo")) + 1)
        return " ".join([year, month.zfill(2), day, time])
