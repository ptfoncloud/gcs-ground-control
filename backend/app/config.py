from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Runtime configuration. Values are read from environment variables
    (case-insensitive) or a `.env` file in `backend/`, falling back to
    the defaults below when unset — e.g. `MAVLINK_CONNECTION_STRING`
    is what docker-compose.yml sets for the backend container.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    MAVLINK_CONNECTION_STRING: str = "udpin:0.0.0.0:14550"
    WS_HEARTBEAT_HZ: float = 20.0
    GESTURE_COOLDOWN_SEC: float = 1.5


settings = Settings()
