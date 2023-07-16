'''Image scrapper console app v0.1

Usage:
    image_scrapper.py URLS...
    image_scrapper.py -f URL_FILE

Options:
    -h           show this message
    -f URL_FILE  specify text file with urls

'''

import re
from pathlib import Path
from typing import Iterable

from docopt import ParsedOptions, docopt
from icecream import ic

from .modules import module_apis


HOST_PATTERN = re.compile('https:\/\/(?:.+\.)?([a-z\-]+)\.[a-z]{3}')

def get_url_host(url: str) -> str:

    search = HOST_PATTERN.search(url)

    if not search:
        return None
    
    return search[1]


def download_from(url: str):

    if url.startswith('#'):
        ic('Skipping escaped line!')
        return
    
    host = get_url_host(url)

    downloader = module_apis.get(host)

    if not downloader:
        ic(f'Unknown url: {url}!')
        return

    downloader.download_from(url)

def download_list(url_list: Iterable[str]):

    for i, url in enumerate(url_list):
        url = url.strip()
        ic(f'[Line {i+1}] - {url}')
        download_from(url)

def main(args: ParsedOptions):

    if (url_file_path := args.f):

        with Path(url_file_path).open() as file:
            download_list(file)

        ic('List download finished!')
        return
    
    for url in args.URLS:
        download_from(url)

def main_cli():
    args = docopt(__doc__)
    main(args)