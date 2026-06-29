import os
import yaml
import json
from dotenv import load_dotenv


class ConfigNode:
    def __init__(self, data: dict):
        for k, v in data.items():
            if isinstance(v, dict):
                setattr(self, k, ConfigNode(v))
            else:
                setattr(self, k, v)

    def to_dict(self):
        def conv(obj):
            # Recursivly convert ConfigNode to dict (including nested ConfigNodes)
            if isinstance(obj, ConfigNode):
                return {k: conv(v) for k, v in obj.__dict__.items()}
            return obj
        return conv(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__dict__})"
    
    def __str__(self) -> str:
        def to_dict(obj):
            if isinstance(obj, ConfigNode):
                return {k: to_dict(v) for k, v in obj.__dict__.items()}
            return obj
        return json.dumps(to_dict(self), indent=2)


class Config:
    env_files = ['.\\.env']
    
    def __init__(self, filepath=None):
        self.filepath = filepath if filepath else os.getenv('CONFIG_FILEPATH')
        self._load_config()

    def _load_config(self):
        # Load env files
        for env_file in self.env_files:
            load_dotenv(env_file)
        
        # Load config.yaml file
        with open(self.filepath, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        self._root = ConfigNode(yaml_data)
    
    def __getattr__(self, item):
        return getattr(self._root, item)
    

    def __repr__(self) -> str:
        return f"Config ({repr(self._root)})"
        
    def __str__(self) -> str:
        str(self._root)


if __name__ == "__main__":
    config = Config()
