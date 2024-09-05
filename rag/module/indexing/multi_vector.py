
import uuid
from typing import List
from rag.connector.base import llm
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_smaller_chunks(documents: List[Document], smaller_chunk_size: int):
    doc_ids = [doc.metadata['id'] for doc in documents]
    tot_docs = []
    child_splitter = RecursiveCharacterTextSplitter(chunk_size=smaller_chunk_size,
                                                    chunk_overlap=0)
    for i, doc in enumerate(documents):
        parent_id = doc_ids[i]
        sub_docs = child_splitter.split_documents([doc])
        for sub_doc in sub_docs:
            sub_doc.metadata['parent_id'] = parent_id
            sub_doc.metadata['id'] = str(uuid.uuid4())
            sub_doc.metadata['multi_vector_type'] = "text small-to-big"
            tot_docs.append(sub_doc)
    return tot_docs


TEXT_SUMMARY_TEMPLATE = """你是一位阅读能手，善于对总结归纳文章段落的摘要。
这些摘要将会被向量化并用于检索召回原始的文章段落，现在请你概括出下面这段话的要点。
文章段落内容: {text} 
总结: """


def generate_text_summaries(documents: List[Document]):
    doc_ids = [doc.metadata['id'] for doc in documents]
    tot_docs = []
    for i, doc in enumerate(documents):
        prompt = PromptTemplate.from_template(TEXT_SUMMARY_TEMPLATE).format(text=doc.page_content)
        parent_id = doc_ids[i]
        summary_doc = Document(llm.invoke(prompt))
        summary_doc.metadata['id'] = str(uuid.uuid4())
        summary_doc.metadata['parent_id'] = parent_id
        summary_doc.metadata['multi_vector_type'] = "text summary"
        tot_docs.append(summary_doc)

    return tot_docs


TABLE_SUMMARY_TEMPLATE = """你是一位阅读能手，善于对总结归纳文章中表格信息的摘要内容。
这些摘要将会被向量化并用于检索召回原始的文章段落，现在请你概括出下面这张表格的要点。
表格内容: {table} 
总结: """


def generate_table_summaries(documents: List[Document]):
    tot_docs = []
    for i, doc in enumerate(documents):
        prompt = PromptTemplate.from_template(TABLE_SUMMARY_TEMPLATE).format(table=doc.page_content)
        summary_doc = Document(llm.invoke(prompt))
        summary_doc.metadata['id'] = str(uuid.uuid4())
        summary_doc.metadata['multi_vector_type'] = "table summary"
        tot_docs.append(summary_doc)

    return tot_docs


