
import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from image_scrapper.api_base import PageParser, ScrapperApi, get_api
from image_scrapper.helpers import read_cookies


@dataclass
class ModuleData:
    page_parser: Callable[[],PageParser]
    headers: dict
    cookies: dict

module_names = tuple(
    module_path.stem for module_path in
        # Get all paths from modules dir
        Path(__file__).absolute().parent.glob('*')
        # If path is python file but not __init__.py
        if module_path.suffix == '.py' and
            module_path.name != '__init__.py'
)

def get_module_data(module_name: str) -> ModuleData:

    module = importlib.import_module(
        f'.{module_name}',
        'image_scrapper.modules'
    )

    if not 'LocalPageParser' in module.__dict__:
        raise TypeError(f'Invalid module: {module}')
    
    page_parser = module.LocalPageParser
    
    headers = {}
    if 'LOCAL_HEADERS' in module.__dict__:
        headers = module.LOCAL_HEADERS
    
    cookies = {}
    if 'LOCAL_COOKIES' in module.__dict__:
        cookies = read_cookies(module.LOCAL_COOKIES)

    return ModuleData(page_parser, headers, cookies)

def get_module_api(module_data: ModuleData) -> ScrapperApi:

    parser = module_data.page_parser
    headers = module_data.headers
    cookies = module_data.cookies
    
    api = get_api(parser, headers, cookies)
    return api
        

modules_data: dict[str, ModuleData] = {
    name: get_module_data(name) for name in module_names
}

module_apis = {
    module_name: get_module_api(module)
        for module_name, module in modules_data.items()
}

__all__ = [
    'module_apis',
]