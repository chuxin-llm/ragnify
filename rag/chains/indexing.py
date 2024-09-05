
import os
import uuid
from typing import List, Union, Tuple, Dict

from langchain_core.documents import Document
from langchain_text_splitters import TextSplitter

from rag.common.utils import run_in_thread_pool, nltk, logger
from rag.module.indexing.splitter import SPLITER_MAPPING
from rag.module.indexing.multi_vector import (
    generate_text_summaries,
    split_smaller_chunks
)

from rag.chains.base import BaseIndexingChain
from rag.connector.vectorstore.base import VectorStoreBase
from rag.connector.database.repository.knowledge_file_repository import (
    delete_file_from_db,
    add_file_to_db,
    add_docs_to_db
)
from rag.connector.database.utils import KnowledgeFile


class IndexingChain(BaseIndexingChain):

    def __init__(self,
                 vectorstore: VectorStoreBase,
                 chunk_size: int,
                 chunk_overlap: int,
                 zh_title_enhance: bool = False,
                 multi_vector_param: Dict = None):
        self.vectorstore = vectorstore
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.zh_title_enhance = zh_title_enhance
        self.multi_vector_param = multi_vector_param

    def load(self,
             file: KnowledgeFile,
             loader: None):
        """
        加载文件内容
        :param file:
        :param loader: 配置加载器，默认根据文件后缀名进行路由，也可指定
        :return:
        """
        if loader is None:
            loader_class = file.document_loader
        else:
            loader_class = loader
        file_path = file.filename if os.path.exists(file.filename) else file.filepath
        docs = loader_class(file_path).load()
        return docs

    def split(self,
              docs: List[Document],
              splitter: Union[str, TextSplitter]):
        if isinstance(splitter, str):
            splitter = SPLITER_MAPPING[splitter]
        chunks = splitter(chunk_size=self.chunk_size,
                          chunk_overlap=self.chunk_overlap).split_documents(documents=docs)
        if not chunks: return []
        for chunk in chunks:
            chunk.metadata["id"] = str(uuid.uuid4())

        smaller_chunk_size = self.multi_vector_param.get("smaller_chunk_size")
        summary = self.multi_vector_param.get("summary")
        multi_vector_chunks = []
        if smaller_chunk_size is not None and int(smaller_chunk_size) > 0:
            multi_vector_chunks.extend(split_smaller_chunks(chunks, smaller_chunk_size))
        if summary:
            multi_vector_chunks.extend(generate_text_summaries(chunks))

        return chunks + multi_vector_chunks

    def file2chunks(self, file, **kwargs) -> Tuple[bool, Tuple[KnowledgeFile, List[Document]]]:
        try:
            docs = self.load(file=file, loader=None)
            chunks = self.split(docs=docs, splitter=file.text_splitter)
            return True, (file, chunks)
        except Exception as e:
            msg = f"从文件 {file.filename} 加载文档时出错：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}', exc_info=e)
            return False, (file, msg)

    def store(self,
              file: KnowledgeFile,
              chunks: List[Document]):

        # step 1. 删除db中该文件相关记录
        del_status = delete_file_from_db(file)

        # step 2. 将docs更新到向量数据库，同样需要将老记录删除
        doc_infos = self.vectorstore.update_doc(file=file,
                                                docs=chunks)

        # shep 3. 将更新后的信息添加到db
        add_db_status = add_file_to_db(file, docs_count=len(chunks)) and \
                        add_docs_to_db(file.kb_name,
                                       file.filename,
                                       doc_infos=doc_infos)
        return del_status and add_db_status

    def chain(self,
              files: List[Union[KnowledgeFile, Tuple[str, str], Dict]], ):
        """
        利用多线程批量将磁盘文件转化成langchain Document，并存储到向量数据库.
        :param files:
        :return: status, (kb_name, file_name, docs | error)
        """
        failed_files = {}
        kwargs_list = []
        for i, file in enumerate(files):
            kwargs = {"file": file}
            kwargs_list.append(kwargs)

        for status, result in run_in_thread_pool(func=self.file2chunks, params=kwargs_list):
            if status:
                file, chunks = result
                chunks = chunks
                self.store(file, chunks)
            else:
                file, error = result
                failed_files[file.filename] = error
        return failed_files


