
import os
from pathlib import Path

from .base import KB_ROOT_PATH
from rag.common.configuration import settings
from rag.module.indexing.splitter import SPLITER_MAPPING, ChineseTextSplitter
from rag.module.indexing.loader import LOADER_MAPPING
from rag.module.utils import get_loader


def get_kb_path(knowledge_base_name: str):
    return os.path.join(KB_ROOT_PATH, knowledge_base_name)


def get_doc_path(knowledge_base_name: str):
    return os.path.join(get_kb_path(knowledge_base_name), "content")


def get_file_path(knowledge_base_name: str, doc_name: str):
    return os.path.join(get_doc_path(knowledge_base_name), doc_name)


class KnowledgeFile:
    def __init__(
            self,
            filename: str,
            knowledge_base_name: str,
    ):
        self.kb_name = knowledge_base_name
        self.filename = str(Path(filename).as_posix())
        self.ext = os.path.splitext(filename)[-1].lower()
        self.filepath = filename if os.path.exists(filename) else get_file_path(knowledge_base_name, filename)
        self.document_loader = self.get_document_loader()
        self.text_splitter = self.get_splitter()

    def get_document_loader(self):
        """根据文件名后缀自动选择Loader"""
        loader_name = ""
        for loader_cls, extensions in LOADER_MAPPING.items():
            if self.ext in extensions:
                loader_name = loader_cls; break
        return get_loader(loader_name)

    def get_splitter(self):
        if settings.text_splitter.splitter_name not in SPLITER_MAPPING:
            return ChineseTextSplitter
        return SPLITER_MAPPING[settings.text_splitter.splitter_name]

    def file_exist(self):
        return os.path.isfile(self.filepath)

    def get_mtime(self):
        return os.path.getmtime(self.filepath)

    def get_size(self):
        return os.path.getsize(self.filepath)