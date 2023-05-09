from typing import Any

import toml

__all__ = ("BotConfig", "DatabaseConfig", "Config", "load_config")

class BotConfig:
    def __init__(self, data: dict[str, Any]):
        self.token: str = data["token"]
        self.default_prefix: str = data["default_prefix"]


class DatabaseConfig:
    def __init__(self, data: dict[str, Any]) -> None:
        self.uri: str = data["uri"]


class Config:
    def __init__(self, data: dict[str, Any]):
        self.bot = BotConfig(data["bot"])
        self.database = DatabaseConfig(data["database"])


def load_config():
    with open("config.toml") as f:
        return Config(dict(toml.load(f)))
