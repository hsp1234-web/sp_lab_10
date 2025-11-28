import yaml
from pathlib import Path

class ConfigManager:
    """
    用於載入和管理策略配置的類別。
    """
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """
        從指定的 YAML 文件載入配置。
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        return config_data

    def get(self, key: str, default=None):
        """
        取得配置值。支持巢狀鍵，例如 'data.api_keys.fred'。
        """
        keys = key.split('.')
        current = self.config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def __getitem__(self, key):
        return self.get(key)
