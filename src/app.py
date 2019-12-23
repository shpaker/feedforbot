from bot.main import main
from bot.core.settings import Settings
import logging

logging.basicConfig(level=logging.DEBUG)
settings = Settings()

# todo add google.fire args and env var CONFIG_FROM_ENV
if __name__ == '__main__':
    main()
