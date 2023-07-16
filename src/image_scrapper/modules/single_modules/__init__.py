
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from icecream import ic

from image_scrapper.api import PageParser, get_api
from image_scrapper.helpers import read_cookies


SELF_PATH = Path(__file__).absolute().parent

@dataclass
class ModuleData:
    page_parser: Callable[[], PageParser]
    headers: dict
    cookies: dict

    def unpack(self):
        return self.page_parser, self.headers, self.cookies
    

def get_module_data(module_name: str) -> ModuleData:
    
    module = importlib.import_module(
        f'.{module_name}', __name__
    )

    try:
        page_parser = module.LocalPageParser
    except AttributeError:
        # TODO: Raise valid error if module is invalid
        raise

    try:
        headers = module.LOCAL_HEADERS
    except AttributeError:
        # ? Log headers not found?
        headers = {}
    
    try:
        cookies = read_cookies(module.LOCAL_COOKIES)
    except AttributeError:
        cookies = {}

    return ModuleData(page_parser, headers, cookies)


module_names = (
    module_path.stem for module_path in SELF_PATH.glob('*')
        if module_path.suffix == '.py' and module_path.stem != '__init__'
)

module_apis = {
    name: get_api(*get_module_data(name).unpack())
        for name in module_names
}

__all__ = [
    'module_apis'
]
