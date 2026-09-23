"""Pluggable alert channels. Configure any mix in config.yaml."""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

import requests

from .trends import Trend


def format_message(niche: str, trends: list[Trend]) -> str:
    lines = [f"Trending in {niche} right now:"]
    for t in trends:
        lines.append(f"- {t.summary()}")
        if t.example_links:
            lines.append(f"  e.g. {t.example_links[0]}")
    return "\n".join(lines)


class ConsoleAlert:
    def send(self, text: str) -> None:
        print(text)


class WebhookAlert:
    """Posts JSON to any webhook. Works with Slack ({"text": ...}) and Discord ({"content": ...})."""

    def __init__(self, url: str, key: str = "text"):
        self.url, self.key = url, key

    def send(self, text: str) -> None:
        requests.post(self.url, json={self.key: text}, timeout=15).raise_for_status()


class TelegramAlert:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token, self.chat_id = bot_token, chat_id

    def send(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        requests.post(url, json={"chat_id": self.chat_id, "text": text,
                                 "disable_web_page_preview": True}, timeout=15).raise_for_status()


class EmailAlert:
    def __init__(self, host: str, port: int, username: str, password: str, to: str, sender: str | None = None):
        self.host, self.port, self.username, self.password = host, int(port), username, password
        self.to, self.sender = to, sender or username

    def send(self, text: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = "Insta Trend Radar alert"
        msg["From"], msg["To"] = self.sender, self.to
        msg.set_content(text)
        with smtplib.SMTP(self.host, self.port) as s:
            s.starttls()
            s.login(self.username, self.password)
            s.send_message(msg)


def _env(value):
    """Allow "${ENV_NAME}" in config so secrets stay out of the YAML file."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.getenv(value[2:-1], "")
    return value


def build_channels(config: list[dict] | None) -> list:
    channels = []
    for c in config or [{"type": "console"}]:
        c = {k: _env(v) for k, v in c.items()}
        kind = c.pop("type")
        if kind == "console":
            channels.append(ConsoleAlert())
        elif kind == "webhook":
            channels.append(WebhookAlert(**c))
        elif kind == "telegram":
            channels.append(TelegramAlert(**c))
        elif kind == "email":
            channels.append(EmailAlert(**c))
        else:
            raise ValueError(f"Unknown alert type: {kind}")
    return channels
