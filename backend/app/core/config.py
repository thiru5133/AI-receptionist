from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./receptionist.db"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MIN: int = 1440

    VAPI_API_KEY: str = ""
    VAPI_WEBHOOK_SIGNING_SECRET: str = ""
    VAPI_PHONE_NUMBER_ID: str = ""

    GOOGLE_SERVICE_ACCOUNT_JSON: str = ""

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_SMS_FROM: str = ""
    TWILIO_WHATSAPP_FROM: str = ""

    PUBLIC_BASE_URL: str = "http://localhost:8000"


settings = Settings()
