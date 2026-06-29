import shutil
import pandas as pd
from datetime import datetime as dt
from pathlib import Path
from abc import ABC, abstractmethod
from collections import defaultdict

from utils.config import ConfigNode

class BaseEndpoint(ABC):

    @property
    @abstractmethod
    def path(self) -> str:
        pass    
    
    @property
    @abstractmethod
    def schema(self) -> dict:
        pass
    
    @property
    @abstractmethod
    def output_format(self) -> list|str:
        # Supported formats: [csv, json, parquet]
        pass

    @property
    @abstractmethod
    def output_schema(self) -> dict:
        pass

    def __init__(self, client, cfg_cls):
        self.client = client
        self.logger = client.logger
        self.cfg_endpoint = self._parse_config(cfg_cls)
        self.output_dir = self._get_output_dir()

    def _parse_config(self, out_cfg_cls=None, cfg_node: ConfigNode | dict = None):
        if cfg_node is None and out_cfg_cls is None:
            raise TypeError("BaseEndpoint._parse_config() must get at lease one input argument")
        
        if not cfg_node:
            ep_name = out_cfg_cls.__name__.removeprefix("Config")
            cfg_node = self.client.cfg_client.endpoints.get(ep_name)

        return self.client._parse_config(out_cfg_cls, cfg_node)
    
    def _get_output_dir(self):
        today = dt.now()
        folder = Path(self.client.output_dir) / self.__class__.__name__ / str(today.year) / str(today.month) / str(today.day)
        if self.cfg_endpoint.override:
            shutil.rmtree(folder)
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    
    @property
    def filename_wo_extension(self):
        # Filename without extension
        return f"batch_{dt.now().strftime("%H%M%S_%f")}"

    def get(self, **kwargs):
        return self.client.request_get(endpoint_path=self.path, **kwargs)
    
    def validate(self, response:dict):
        rc = True
        for field, dtype in self.schema.items():
            if field not in response:
                self.logger.warnning(f"Missing required field '{field}' in API response")
                rc = False
            if not isinstance(response[field], dtype):
                self.logger.warnning(f"Required field '{field}' dtype must be '{dtype}', curretly '{type(response[field])}'")
                rc = False
        return rc

    def save_batch(self, batch: list) -> bool:
        # return rc=True if data was saved in at least one format
        if not batch:
            self.logger.info("No data to save, empty batch")
            return 
        rc = defaultdict(list)
        filename_wo_ext = self.filename_wo_extension
        
        # Output formts handlers
        fmt_handlers = {
            "csv":     lambda df, filepath: df.to_csv(filepath, index=False), 
            "json":    lambda df, filepath: df.to_json(filepath, orient="records", indent=2), 
            "parquet": lambda df, filepath: df.to_parquet(filepath, index=False),
            }

        # Validate output format(s)
        if isinstance(self.output_format, str):
            self.output_format = [self.output_format]
        
        self.logger.info(f"Saving data: output_format={self.output_format}, output_dir='{self.output_dir}'")

        df = pd.concat(batch).astype(self.output_schema)
        
        fmt_opts = list(fmt_handlers.keys())
        for fmt in self.output_format:
            
            if fmt not in fmt_opts:
                self.logger.warning(f"Output format '{fmt}' is not supported. Supported: {fmt_opts}")
                continue
            
            filepath = self.output_dir / (filename_wo_ext + f".{fmt}")
            fmt_handlers[fmt](df, filepath)
            rc[filepath.exists()].append(fmt)
        
        if False in rc:
            if True in rc:
                self.logger.warning(f"data saved successfully in format(s): {rc[True]}, and failed in format(s): {rc[False]}")
            else:
                self.logger.error(f"Failed to save data in all format(s): output_format={self.output_format}")
                raise FileNotFoundError(f"No output file found in output dir '{self.output_dir}'")
        else:
            self.logger.info(f"All file format(s) saved succesfully!")

    @abstractmethod
    def run(self):
        raise NotImplemented("Subclasses must implement 'save ' method")
        