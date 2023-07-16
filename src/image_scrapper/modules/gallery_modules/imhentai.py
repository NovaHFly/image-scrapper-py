
from string import Template

from image_scrapper.api import GalleryParseParams
from image_scrapper.constants.paths import DOWNLOADS

LOCAL_PARSE_PARAMS = GalleryParseParams(
    title_header_selector='h1',
    page_count_selector='.pages',

    big_img_selector='#gimg',
    big_img_attr='data-src',

    download_dir=DOWNLOADS / 'imhentai',
    template_url=Template('https://imhentai.xxx/view/$gal_id/$page_n')
)

__all__ = [
    'LOCAL_PARSE_PARAMS',
]