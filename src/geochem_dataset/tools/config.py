import configparser
import os

from appdirs import AppDirs

from .. import __app_name__, __app_author__, __app_version__

CONFIG_FILE_NAME = 'config.ini'


class ConfigParser(configparser.ConfigParser):
    def __init__(self, *args, **kwargs):
        app_dirs = AppDirs(kwargs['app_name'], kwargs['app_author'], version=kwargs['app_version'])
        self._config_path = os.path.join(app_dirs.user_config_dir, kwargs['config_file_name'])

        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)

        del kwargs['app_name'], kwargs['app_author'], kwargs['app_version'], kwargs['config_file_name']
        super().__init__(*args, **kwargs)

        self.load()

    def load(self):
        if not os.path.exists(self._config_path):
            self.save()

        with open(self._config_path, 'r') as f:
            self.read_file(f)

    def save(self):
        with open(self._config_path, 'w') as f:
            self.write(f)


config = ConfigParser(
    app_name=__app_name__,
    app_author=__app_author__,
    app_version=__app_version__,
    config_file_name=CONFIG_FILE_NAME
)
