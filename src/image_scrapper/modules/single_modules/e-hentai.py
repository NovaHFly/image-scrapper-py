
from bs4 import BeautifulSoup as bs
from icecream import ic

from image_scrapper.constants.paths import DOWNLOADS
from image_scrapper.api import (
    GalleryApi, GalleryParseParams
)


class LocalApi(GalleryApi):

    parse_params = GalleryParseParams(
        title_header_selector='h1',
        page_count_selector='.ptt td:nth-last-of-type(2) a',

        big_img_selector='#i3 img',
        big_img_attr='src',

        download_dir=DOWNLOADS / 'e-hentai',
    )
    
    def generate_page_urls(self, page_count: int) -> list[str]:
        
        for i in range(page_count):
            
            g_page_url = self.current_url + f'?p={i}'
            g_page_res = self.get(g_page_url)

            ic(f'Got page {i+1}!')

            soup = bs(g_page_res.text, 'lxml')

            images_list_tag = soup.select_one('#gdt')

            for image_tag in images_list_tag.select('.gdtm a'):
                yield image_tag.attrs['href']

__all__ = [
    'LocalApi',
]