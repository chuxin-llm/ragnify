
import json
from fastapi import Body
from typing import List, Tuple
from sse_starlette.sse import EventSourceResponse

from server.knowledge import KBServiceFactory
from server.utils import BaseResponse
from rag.chains.retrieval import RetrievalChain
from rag.chains.generate import GenerateChain
from rag.connector.utils import get_vectorstore
from rag.connector.base import llm, embedding_model
from rag.module.base import reranker
from rag.common.configuration import settings


async def knowledge_base_chat(query: str = Body(..., description="用户输入", examples=["你好"]),
                             knowledge_base_name: str = Body(..., description="知识库名称", examples=["rag"]),
                             history: List[Tuple[str, str]] = Body(
                                  [],
                                  description="历史对话",
                                  examples=[[("user", "我们来玩成语接龙，我先来，生龙活虎"),
                                             ("assistant", "虎头虎脑")]]
                              ),
                             score_threshold: float = Body(0.0, description="相似度阈值"),
                             topk: int = Body(5, description="检索召回的相似度文档数量"),
                             stream: bool = Body(True, description="流式输出"),
                             return_docs: bool = Body(False, description="返回检索结果"),):
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    vector_store = get_vectorstore(knowledge_base_name=knowledge_base_name,
                                   vs_type=settings.vector_store.type,
                                   embed_model=embedding_model)

    # 知识库召回上下文
    retrieval_chain = RetrievalChain(vectorstore=vector_store,
                                     reranker=reranker,
                                     score_threshold=score_threshold,
                                     top_k=topk)
    docs = [doc["document"] for doc in retrieval_chain.chain(query=query)]

    # LLM generate
    generate_chain = GenerateChain(llm=llm, stream=stream)
    results = {} if not return_docs else {"docs": [{"filename": d.metadata.get("filename"), "context": d.page_content, "similarity_score": d.score} for d in docs]}

    async def iterator():
        res_generator = generate_chain.chain(query=query, docs=docs, history=history)
        for ans in res_generator:
            results.update({"result": ans})
            yield json.dumps(results, ensure_ascii=False)
    return EventSourceResponse(iterator())

