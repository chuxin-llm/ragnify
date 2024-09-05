
import os

from typing import List, Tuple, Dict
from fastapi import Body
from langsmith import traceable
from langchain_core.documents import Document
from langchain_core.messages.chat import ChatMessage
from langchain.prompts.chat import ChatPromptTemplate
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from rag.common.utils import settings
from rag.chains.retrieval import RetrievalChain
from rag.chains.generate import GenerateChain
from rag.connector.utils import get_vectorstore
from rag.connector.base import llm, embedding_model
from rag.module.base import reranker

from server.knowledge import KBServiceFactory
from server.utils import BaseResponse


os.environ["LANGCHAIN_API_KEY"] = settings.langchain.langchain_api_key
os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain.langchain_endpoint
os.environ["LANGCHAIN_TRACING_V2"] = settings.langchain.langchain_tracing_v2
os.environ["LANGCHAIN_PROJECT"] = settings.langchain.langchain_project


def trace_rag_pipeline(query: str = Body(..., description="用户输入", examples=["你好"]),
                       knowledge_base_name: str = Body(..., description="知识库名称", examples=["rag"]),
                       history: List[Tuple[str, str]] = Body(
                           [],
                           description="历史对话",
                           examples=[[("user", "我们来玩成语接龙，我先来，生龙活虎"),
                                      ("assistant", "虎头虎脑")]]),
                       ):
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name)
    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    # init components
    vector_store = get_vectorstore(knowledge_base_name,
                                   settings.vector_store.type,
                                   embedding_model)
    generate_chain = GenerateChain(llm=llm, stream=False)
    retrieval_chain = RetrievalChain(vectorstore=vector_store,
                                     reranker=reranker,
                                     score_threshold=0.)

    @traceable(run_type="retriever", name="Pre Retrieval")
    def pre_retrieval(question: str) -> List[str]:
        return retrieval_chain.pre_retrieval(question)

    @traceable(run_type="retriever", name="Retrieval")
    def retrieval(questions: List[str]) -> Dict[str, List[Document]]:
        org_question, expand_questions = questions[0], questions[1:]
        docs = retrieval_chain.retrieval(org_question)
        for i, q in enumerate(expand_questions):
            q_docs = retrieval_chain.retrieval(q)
            for r_k in q_docs:
                if r_k in docs: docs[str(i+1) + "_" + r_k] = q_docs[r_k]
        return docs

    @traceable(run_type="retriever", name="Post Retrieval")
    def post_retrieval(question: str, docs: Dict[str, List[Document]]) -> List[Document]:
        return retrieval_chain.post_retrieval(question, docs)

    @traceable(run_type="chain", name="Retrieval Chain")
    def retriever(question: str) -> List[Document]:
        expand_questions = pre_retrieval(question)
        docs = retrieval([question] + expand_questions)
        return [doc["document"] for doc in post_retrieval(question, docs)]

    @traceable(run_type="prompt", name="Augment Context")
    def augment_context(question: str,
                        retrieval_docs: List[Document],
                        history: List[Tuple[str, str]]):
        messages = [{"role": h[0], "content": h[1]} for h in history] + [
            {"role": "user", "content": generate_chain.augment(question, retrieval_docs)}
        ]
        return messages

    @traceable(run_type="llm", name="LLM Call")
    def llm_call(messages):
        messages = [ChatMessage(role=ms["role"], content=ms["content"]) for ms in messages]
        prompt = ChatPromptTemplate.from_messages(messages).format_prompt().to_string()
        res_generator = generate_chain.generate(prompt=prompt)
        res = ""
        for ans in res_generator: res = ans
        # chat_completion = generate_chain.generate(prompt=prompt)
        chat_completion = {"choices": [
            Choice(
                finish_reason='stop',
                index=0,
                logprobs=None,
                message=ChatCompletionMessage(
                    content=res, role='assistant', function_call=None, tool_calls=None
                )
            )
        ]}
        return chat_completion

    @traceable(run_type="chain", name="Augmented Generate")
    def generator(question: str, docs: List[Document], history: List[Tuple[str, str]]):
        messages = augment_context(question, docs, history)
        chat_completion = llm_call(messages)
        return chat_completion["choices"][0].message.content

    @traceable(name="Rag Pipeline Traceable")
    def chat_pipeline(question: str):
        retrieval_docs = retriever(question)
        result = generator(question, retrieval_docs, history)
        return result

    chat_pipeline(query)

    return BaseResponse(code=200, msg=f"Tracing success!")