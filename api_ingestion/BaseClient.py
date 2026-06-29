import logging
import requests
import shutil
from urllib3.util.retry import Retry
from pydantic import BaseModel, Field, ValidationError
from urllib.parse import urljoin
from abc import ABC, abstractmethod
from requests.adapters import HTTPAdapter
from importlib import import_module
from pathlib import Path

from utils.config import Config, ConfigNode
from utils.logger import AppLogger


class ConfigBaseClient(BaseModel):
    retries:          int   = Field(3, description="Num retries for API requests")
    backoff_factor:   float = Field(0.5, description="Base delay used for exponential backoff")
    status_forcelist: list  = Field([429, 500, 502, 503, 504], description="List of HTTP status codes that should trigger a retry")
    allowed_methods:  list  = Field(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"], description="List of HTTP methods that are allowed to be retried")
    raise_on_status:  bool  = Field(False, description="raise an exception when a retryable status code is encountered")
    base_output_dir:  str   = Field("outputs", description="dir for saving output files")


class BaseClient(ABC):
    
    @property
    @abstractmethod
    def base_url(self):
        pass
    
    def __init__(self, default_headers: dict | None = None, cfg_cls=None):
        self.cfg     = Config()
        self.logger  = AppLogger(self.cfg.logger).get()
        
        self.cfg_base_client = self._parse_config(ConfigBaseClient)
        self.default_headers = default_headers or {}
        self.session = self._create_session()
        
        self.cfg_client = self._parse_config(cfg_cls)
        self.output_dir = self._get_output_dir()
    
    def _parse_config(self, out_cfg_cls=None, cfg_node: ConfigNode | dict = None):
        if cfg_node is None and out_cfg_cls is None:
            raise TypeError("BaseClient._parse_config() must get at lease one input argument")
        
        if cfg_node:
            if isinstance(cfg_node, ConfigNode):
                config_dict = cfg_node.to_dict()
            else:
                config_dict = cfg_node
        else:
            client_name = out_cfg_cls.__name__.removeprefix("Config")
            cfg_node = getattr(self.cfg.clients, client_name)
            return self._parse_config(out_cfg_cls=out_cfg_cls, cfg_node=cfg_node)
        
        if out_cfg_cls is None:
            return config_dict
        
        try:
            return out_cfg_cls(**config_dict)
        except ValidationError as e:
            self.logger.error(f"Failed to load '{out_cfg_cls.__name__}': {e}")
            raise

    def _create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=self.cfg_base_client.retries,                      # max num of retry attempts
            backoff_factor=self.cfg_base_client.backoff_factor,      # delay between retries using exponential backoff
            status_forcelist=self.cfg_base_client.status_forcelist,  # HTTP status codes that should trigger a retry
            allowed_methods=self.cfg_base_client.allowed_methods,    # HTTP methods that are allowed to be retried
            raise_on_status=self.cfg_base_client.raise_on_status,    # raise an exception when a retryable status code is encountered
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update(self.default_headers)
        return session
    
    def _get_output_dir(self):
        folder = Path(self.cfg_base_client.base_output_dir) / self.__class__.__name__
        if self.cfg_client.override: 
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    
    def get_active_endpoints(self, module_path: str, endpoints_config: dict[str: dict]) -> list:
        """
        Import active endpoints handlers
        path - path to dir containing endpoints handlers
        endpoints_toggle - determins which endpoints are enabled / disabled
        handler name in the config should match module name (.py file without extension) and handler class in the module
        """
        self.logger.info(f"Importing enabled endpoints handlers from path: '{module_path}'")
        active_endpoints = {}
        for ep_name, ep_config in endpoints_config.items():
            if not ep_config.get('is_enabled', False):
                continue
            try:
                module = import_module(f"{module_path}.{ep_name}")
                cls = getattr(module, ep_name)
                active_endpoints[ep_name] = cls(self)
                self.logger.info(f"Loaded endpoint: {ep_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load endpoint '{ep_name}', Skipping. error: {e}")
        
        if not active_endpoints:
            self.logger.error("Failed to load ALL active endpoint module")
            raise ModuleNotFoundError("Failed to load ALL active endpoint module")

        return active_endpoints

    def request_get(self, endpoint_path: str, **kwargs) -> dict:
        url = urljoin(self.base_url + "/", endpoint_path.lstrip("/"))
        # self.logger.info(f"GET url: '{url}'")
        response = self.session.get(url, **kwargs)
        
        if not response.ok:
            logging.error(f"FAIL GET request: {response.status_code} {response.text}")
            return {}
        return response.json()

        # page = 1
        # all_data_pages = []
        # self.logger.info("Start paginated data fetching")
        # while True:
        #     response = self.session.get(url, params={"page": page}) #, headers=headers, **kwargs)
        #     data = response.json()

        #     if not response.ok:
        #         logging.error(f"FAIL page {page}: {response.status_code} {response.text}")
        #         continue

        #     all_data_pages.append(data)
            
        #     if page >= data.get("total_pages", 1):
        #         self.logger.info(f"Reached last page / API page limit: {page} / {data.get("total_pages", 1)}")
        #         break
        #     if page_limit and page >= page_limit:
        #         self.logger.info(f"Reached defined page limit: {page} / {page_limit}")
        #         break
        #     if page % 50 == 0:
        #         self.logger.info(F"SUCCESS {page} pages: status_code={response.status_code}")
            
        #     page += 1

        # return all_data_pages
    
    @abstractmethod
    def run(self):
        raise NotImplemented("Subclasses must implement 'run' method")
