
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from image_scrapper.api import get_api, ScrapperApi
from image_scrapper.helpers import read_cookies

import httpx


SELF_PATH = Path(__file__).absolute().parent

def is_module(path: Path) -> bool:
    """Checks if path provided corresponds to supported module.
    
    Application supports single python files and python packages."""
    
    # Valid module name does not start with undescore
    if path.name.startswith('_'):
        return False
    
    # Single python file module
    if path.suffix == '.py' and not path.stem == '__init__':
        return True
    
    # Python package module
    if path.is_dir() and path.glob('__init__.py'):
        return True
    
    return False
    

@dataclass
class ModuleData:

    api_class: Callable[[httpx.Client], ScrapperApi]
    headers: dict
    cookies: dict

    def unpack(self):
        return self.api_class, self.headers, self.cookies
    

def get_module_data(module_name: str) -> ModuleData:
    
    module = importlib.import_module(
        f'.{module_name}', __name__
    )

    try:
        api_class = module.LocalApi
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

    return ModuleData(api_class, headers, cookies)


module_names = (
    module_path.stem for module_path in SELF_PATH.glob('*')
        if is_module(module_path)
)

module_apis = {
    name: get_api(*get_module_data(name).unpack())
        for name in module_names
}

__all__ = [
    'module_apis'
]
