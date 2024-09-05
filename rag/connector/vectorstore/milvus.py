
from __future__ import annotations
from typing import List
import hashlib
import uuid
import operator

from pymilvus import MilvusClient
from langchain.docstore.document import Document
from langchain_core.embeddings import Embeddings
from langchain.vectorstores.milvus import Milvus

from rag.connector.database.utils import KnowledgeFile
from rag.connector.vectorstore.base import VectorStoreBase
from rag.common.configuration import settings
from rag.common.utils import logger


def md5_encryption(data):
    md5 = hashlib.md5()
    md5.update(data.encode('utf-8'))
    return md5.hexdigest()


class MilvusVectorStore(VectorStoreBase):

    def __init__(self,
                 embedding_model: Embeddings,
                 collection_name: str):
        self.embeddings = embedding_model
        self.knowledge_base_name = collection_name
        self.collection_name = collection_name
        self.config = settings.vector_store
        self.milvus = None

        self._load_milvus()

    def _load_milvus(self):
        connection_args = {
            "host": self.config.host,
            "port": self.config.port,
            "user": self.config.user,
            "password": self.config.password,
            "secure": False,
        }
        index_params = self.config.kwargs.get("index_params", None)
        search_params = self.config.kwargs.get("search_params", None)
        # langchain client
        self.milvus = Milvus(self.embeddings,
                             collection_name=self.collection_name,
                             connection_args=connection_args,
                             index_params=index_params,
                             search_params=search_params,
                             metadata_field="metadata",
                             auto_id=False)
        self.pyclient = MilvusClient(
            uri="http://"+self.config.host+":"+self.config.port
        )

    def create_vectorstore(self):
        """ 注意langchain.milvus 初始化时不会真正创建Collection
        """
        init_kwargs = {"embeddings": self.embeddings.embed_documents(["初始化"]),
                       "metadatas": [{}],
                       "partition_names": None,
                       "replica_number": 1,
                       "timeout": None}
        self.milvus._init(**init_kwargs)

    def drop_vectorstore(self):
        if self.pyclient.has_collection(self.collection_name):
            self.pyclient.release_collection(self.collection_name)
            self.pyclient.drop_collection(self.collection_name)

    def clear_vectorstore(self):
        if self.pyclient.has_collection(self.collection_name):
            self.pyclient.release_collection(self.collection_name)
            self.pyclient.drop_collection(self.collection_name)
            self._load_milvus()

    def delete_doc(self, filename):
        """
        删除指定文件的所有chunk记录
        :param filename:
        :return:
        """
        if self.pyclient.has_collection(self.collection_name):
            delete_list = [item.get("pk") for item in
                           self.pyclient.query(collection_name=self.collection_name,
                                               filter=f'metadata["source"] == "{md5_encryption(filename)}"',
                                               output_fields=["pk"])]

            if len(delete_list) > 0:
                self.pyclient.delete(collection_name=self.collection_name,
                                     filter=f'pk in {delete_list}')
                logger.warning(f"成功删除文件 {filename} {str(len(delete_list))} 条记录")
            else:
                logger.warning(f"vs中不存在文件 {filename} 相关的记录，不需要删除")
        else:
            logger.warning(f"vs为空，没有可删除的记录")

    def update_doc(self, file: KnowledgeFile, docs: List[Document]):
        """
        插入/更新向量数据库中的记录
        更新：若该文件的chunk已经存在，需要先将原信息删除后重新插入
        :param file:
        :param docs:
        :return:
        """
        self.delete_doc(file.filename)
        return self.add_doc(file, docs=docs)

    def add_doc(self, file: KnowledgeFile, docs, **kwargs):
        """
        将chunks插入vs
        :param file:
        :param docs:
        :return:
        """
        # 将所有信息存储到metadata
        doc_ids = []
        for doc in docs:
            doc.metadata["source"] = md5_encryption(file.filename)
            doc.metadata["filename"] = file.filename
            # doc.metadata.setdefault("source", md5_encryption(file.filename))    # source存储文件名
            for k, v in doc.metadata.items():
                doc.metadata[k] = str(v)
            for field in self.milvus.fields:
                doc.metadata.setdefault(field, "")
            doc.metadata.pop(self.milvus._text_field, None)
            doc.metadata.pop(self.milvus._vector_field, None)
            doc_id = doc.metadata.get("id", str(uuid.uuid4()))
            doc_ids.append(doc_id)
        ids = self.milvus.add_documents(docs) if len(doc_ids) == 0 else self.milvus.add_documents(docs, **{"ids": doc_ids})
        doc_infos = [{"id": id, "metadata": doc.metadata} for id, doc in zip(ids, docs)]

        return doc_infos

    def search_docs(self, text, top_k, threshold, **kwargs):
        """
        :param text:
        :param top_k:
        :param threshold:
        :return: List[Tuple[Document, float]]: Result doc and score.
        """

        docs = self.milvus.similarity_search_with_score(query=text,
                                                        k=top_k,
                                                        **kwargs)
        if threshold is not None:
            docs = self._score_threshold_process(docs, threshold, top_k)

        # 兼容multi_vector，召回父文档
        parent_doc_map = {}         # retrieval_index: parent_id
        for i, tp in enumerate(docs):
            parent_id = tp[0].metadata.get("parent_id")
            if parent_id is not None: parent_doc_map[i] = parent_id

        if len(parent_doc_map) > 0:
            try:
                ids = list(set(parent_doc_map.values()))
                parent_docs = {}        # parent_id: parent_doc
                for p_doc in self.pyclient.get(collection_name=self.collection_name,
                                               ids=ids,
                                               output_fields=["pk", "text", "metadata"]):
                    parent_docs[p_doc["pk"]] = Document(page_content=p_doc["text"],
                                                        metadata=p_doc["metadata"])
                for doc_index in parent_doc_map:
                    docs[doc_index] = tuple([parent_docs[parent_doc_map[doc_index]], docs[doc_index][1]])

            except Exception as e:
                msg = f"路由到parent chunk失败：{e}"
                logger.error(f'{e.__class__.__name__}: {msg}', exc_info=e)

        return docs

    def _score_threshold_process(self, docs, score_threshold, k):
        if score_threshold is not None:
            cmp = (
                operator.ge
            )
            docs = [
                (doc, similarity)
                for doc, similarity in docs
                if cmp(similarity, score_threshold)
            ]
        return docs[:k]

