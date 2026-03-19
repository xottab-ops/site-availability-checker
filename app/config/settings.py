from typing import Any, Tuple, Type

from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.main import PydanticBaseSettingsSource
from pydantic_settings.sources import EnvSettingsSource, DotEnvSettingsSource


class _CommaSeparatedMixin:
    """Позволяет читать list[str] как через JSON, так и через запятые."""

    def decode_complex_value(self, field_name: str, field_info: FieldInfo, value: Any) -> Any:
        import json
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return [s.strip() for s in str(value).split(",") if s.strip()]


class _CommaSeparatedEnvSource(_CommaSeparatedMixin, EnvSettingsSource):
    pass


class _CommaSeparatedDotEnvSource(_CommaSeparatedMixin, DotEnvSettingsSource):
    pass


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    bot_token: str
    alarm_chat_id: str
    log_chat_id: str | None = None
    sites: list[str]
    check_interval: int = 60
    page_timeout: int = 30000
    http_error_threshold: int = 400
    notify_interval: int = 600

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        **kwargs: Any,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        env_file = cls.model_config.get("env_file", ".env")
        init_settings = kwargs.get("init_settings")
        return (
            init_settings,
            _CommaSeparatedEnvSource(settings_cls),
            _CommaSeparatedDotEnvSource(settings_cls, env_file=env_file),
        )


settings = Settings()
