
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Callable

import httpx
from icecream import ic

from image_scrapper.helpers import replace_win_path_symbols, retry_times

# ? Not sure if using different user agent will always allow to bypass
# ?  bot checks. Most likely if something is blocked by cloudflare check
# ?  it won't help
BASE_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3542.0 Safari/537.36',
}

BASE_SUCCESS_MESSAGE = '{} download finished: {}!'

class UnloggedError(Exception):
    ...


def construct_package_name(
        pack_id: str, title: str, *,
        author: str|None = None,
        file_extension: str|None = None,
        add_counter: bool = False) -> str:
    
    package_name = f'{title}'

    if author:
        package_name += f' by {author}'
    
    package_name += f' - {pack_id}'

    if add_counter:
        package_name += '[{}]'
    
    if file_extension:
        package_name += f'.{file_extension}'

    return package_name


@dataclass
class DownloadUnit:
    """A download unit. Used by downloader
    
    Attrs:
    kind: str - kind of download ("file", "text") [Default: file];
    contents: str - contents of download. Can contain file url or some text;
    file_path: Path - where to save download unit contents"""
    
    contents: str
    file_path: Path
    kind: str = 'file'

# ^ All of package dataclasses are abstract,
# ^ as contents property is not defined!

class DownloadPackage(ABC):
    
    @property
    @abstractmethod
    def contents(self) -> Iterable[DownloadUnit]:
        """Sequence of download units"""
        ...

    def __post_init__(self):
        
        # ! Replace with debug logging
        ic(self)

@dataclass
class BasicPackage(DownloadPackage):

    id: str
    title: str

    def __post_init__(self):
        self.title = replace_win_path_symbols(self.title)
        return super().__post_init__()

@dataclass
class AuthorPackage(BasicPackage):

    author: str

    def __post_init__(self):
        self.author = replace_win_path_symbols(self.author)
        return super().__post_init__()

# ^ ------------------------------------------------

class PageParser(ABC):
    
    def set_parent_api(self, parent_api: 'ScrapperApi'):
        self.parent_api = parent_api

    @abstractmethod
    def parse(self, response: httpx.Response) -> DownloadPackage:
        ...

@dataclass
class ScrapperApi:

    client: httpx.Client
    parser: PageParser

    @retry_times(5)
    def get_response(self, url: str):
        """Allows for request repeating on exception"""
        return self.client.get(url)

    def _download_package(self, package: DownloadPackage):

        for unit in package.contents:

            contents = unit.contents
            file_path = unit.file_path
            file_path.parent.mkdir(exist_ok=True, parents=True)

            if unit.kind == 'text':
                self._write_text(contents, file_path)
                continue

            if unit.kind == 'file':
                self._download_file(contents, file_path)
                continue

    def _write_text(self, text: str, to_path: Path):
        
        success_message = BASE_SUCCESS_MESSAGE.format('Text', to_path)

        with to_path.open('w', encoding='UTF-8') as file:
            file.write(text)

        ic(success_message)

    def _download_file(self, from_url: str, to_path: Path):
        """Downloads one file"""

        success_message = BASE_SUCCESS_MESSAGE.format('File', to_path)
        
        with self.client.stream('GET', from_url) as stream:
            ic(stream)

            with to_path.open('wb') as file:
                for byte in stream.iter_bytes():
                    file.write(byte)

        ic(success_message)

    def download_from(self, url: str):
        
        response = self.get_response(url)

        try:
            package = self.parser.parse(response)
        except UnloggedError:
            ic('Please, restart program!')
            exit(1)
            
        self._download_package(package)


def get_api(
        page_parser: Callable[[], PageParser],
        headers: dict = {}, cookies: dict = {},
        ) -> ScrapperApi:
    
    
    client = httpx.Client(
        headers=BASE_HEADERS | headers, cookies=cookies,
        follow_redirects=True)
    
    parser = page_parser()
    
    api = ScrapperApi(client, parser)
    parser.set_parent_api(api)
    
    return api


__all__ = [
    'DownloadUnit',
    'BasicPackage',
    'AuthorPackage',
    'DownloadPackage',
    'ScrapperApi',
    'PageParser',
    'construct_package_name',
    'UnloggedError',
    'get_api',
]