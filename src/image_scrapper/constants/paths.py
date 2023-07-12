
from pathlib import Path

APP_DATA = Path('Data')

DOWNLOADS = APP_DATA / 'Downloads'
COOKIES = APP_DATA / '.cookies'

__all__ = [
    'DOWNLOADS',
    'COOKIES'
]