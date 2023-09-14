from abc import ABC, abstractmethod
from PIL import Image


class Storage(ABC):
    @abstractmethod
    def make_dirs(self, dir_path):
        pass

    @abstractmethod
    def list_files(self, dir_path, pattern):
        pass

    @abstractmethod
    def write_json(self, data, file_path):
        pass

    @abstractmethod
    def read_json(self, file_path):
        pass

    @abstractmethod
    def write_image(self, image: Image, file_path):
        pass

    @abstractmethod
    def read_file(self, file_path):
        pass
