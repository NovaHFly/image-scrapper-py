
import importlib
from pathlib import Path

from image_scrapper.api import (
    GalleryParseParams, GalleryParser, get_api)


SELF_PATH = Path(__file__).absolute().parent

def get_parse_params(module_name: str) -> GalleryParseParams:
    
    module = importlib.import_module(
        f'.{module_name}', __name__
    )

    try:
        parse_params = module.LOCAL_PARSE_PARAMS
    except AttributeError:
        # TODO: Raise valid error if module is invalid
        raise

    return parse_params

module_names = (
    module_path.stem for module_path in SELF_PATH.glob('*')
        if module_path.suffix == '.py' and module_path.stem != '__init__'
)

module_apis = {
    name: get_api(
        GalleryParser().set_parse_params(
            get_parse_params(name)
        )
    ) for name in module_names
}
