"""Development-only notification outbox; production delivery remains a provider concern."""

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class DevelopmentMessage:
    purpose: str
    recipient: str
    value: str


class DevelopmentNotificationProvider:
    """Keeps delivery values in process memory and never writes them to logs."""

    def __init__(self) -> None:
        self._messages: list[DevelopmentMessage] = []

    def deliver(self, purpose: str, recipient: str, value: str) -> None:
        if settings.app_env.lower() != "production":
            self._messages.append(DevelopmentMessage(purpose, recipient, value))

    def messages(self) -> list[DevelopmentMessage]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()


development_notifications = DevelopmentNotificationProvider()
