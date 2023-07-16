
from .single_modules import module_apis as single_apis
from .gallery_modules import module_apis as gallery_apis

module_apis = single_apis | gallery_apis

__all__ = [
    'module_apis'
]