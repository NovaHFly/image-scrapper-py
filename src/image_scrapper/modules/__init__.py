
import importlib
from typing import Protocol
from pathlib import Path

from image_scrapper.api_base import get_api, PageParser
from image_scrapper.helpers import read_cookies


class DownloaderModule(Protocol):
    PageParser: PageParser
    LOCAL_HEADERS: dict | None
    LOCAL_COOKIES: Path | None

module_names = tuple(
    module_path.stem for module_path in
        # Get all paths from modules dir
        Path(__file__).absolute().parent.glob('*')
        # If path is python file but not __init__.py
        if module_path.suffix == '.py' and
            module_path.name != '__init__.py'
)

def import_plugin_module(module_name: str) -> DownloaderModule:
    return importlib.import_module(f'.{module_name}', 'image_scrapper.modules')

def get_module_api(module: DownloaderModule):

    headers = module.LOCAL_HEADERS \
        if 'LOCAL_HEADERS' in module.__dict__ else {}
    
    cookies = read_cookies(module.LOCAL_COOKIES) \
        if 'LOCAL_COOKIES' in module.__dict__ else {}
    
    api = get_api(module.PageParser, headers, cookies)

    return api
        

loaded_modules: dict[str, DownloaderModule] = {
    name: import_plugin_module(name) for name in module_names
}

module_api_list = {
    module_name: get_module_api(module)
        for module_name, module in loaded_modules.items()
}

__all__ = [
    'module_api_list',
]