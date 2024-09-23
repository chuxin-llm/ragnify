
import os

from typing import List, Tuple, Dict
from fastapi import Body
from langfuse.decorators import observe, langfuse_context
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

from server.knowledge import KBServiceFactory
from server.utils import BaseResponse

os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse.langfuse_secret_key
os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse.langfuse_public_key
os.environ["LANGFUSE_HOST"] = settings.langfuse.langfuse_host


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
                                     score_threshold=0.)

    @observe(name="Pre Retrieval")
    def pre_retrieval(question: str) -> List[str]:
        res = retrieval_chain.pre_retrieval(question)
        langfuse_context.update_current_observation(
            input=question, output=res
        )
        return res

    @observe(name="Retrieval")
    def retrieval(questions: List[str]) -> Dict[str, List[Document]]:
        org_question, expand_questions = questions[0], questions[1:]
        docs = retrieval_chain.retrieval(org_question)
        for i, q in enumerate(expand_questions):
            q_docs = retrieval_chain.retrieval(q)
            for r_k in q_docs:
                if r_k in docs: docs[str(i + 1) + "_" + r_k] = q_docs[r_k]

        input = {"用户输入问题": org_question, "": expand_questions} if expand_questions else {
            "用户输入问题": org_question}
        output = {}
        for rk in docs:
            output[rk] = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs[rk]]

        langfuse_context.update_current_observation(
            input=input,
            output=output
        )
        return docs

    @observe(name="Post Retrieval")
    def post_retrieval(question: str, docs: Dict[str, List[Document]]) -> List[Document]:
        res = retrieval_chain.post_retrieval(question, docs)
        langfuse_context.update_current_observation(
            input={"用户输入问题": question, "检索召回的文档集合": docs},
            output={f"重排序后的的第{i + 1}个文档": {"page_content": doc["document"].page_content,
                                                     "metadata": doc["document"].metadata} for i, doc in enumerate(res)}
        )
        return res

    @observe(name="Retrieval Chain")
    def retriever(question: str) -> List[Document]:
        expand_questions = pre_retrieval(question)
        docs = retrieval([question] + expand_questions)
        post_docs = [doc["document"] for doc in post_retrieval(question, docs)]
        langfuse_context.update_current_observation(
            input=question,
            output={f"检索召回的第{i + 1}个文档": {"page_content": doc.page_content, "metadata": doc.metadata} for
                    i, doc in enumerate(post_docs)}
        )
        return post_docs

    @observe(name="Augment Context")
    def augment_context(question: str,
                        retrieval_docs: List[Document],
                        history: List[Tuple[str, str]]):
        messages = [{"role": h[0], "content": h[1]} for h in history] + [
            {"role": "user", "content": generate_chain.augment(question, retrieval_docs)}
        ]
        langfuse_context.update_current_observation(
            input={"用户输入问题": question, "检索召回的文档": retrieval_docs},
            output=messages
        )
        return messages

    @observe(name="LLM Call", as_type="generation")
    def llm_call(messages):
        input_ms = messages.copy()
        messages = [ChatMessage(role=ms["role"], content=ms["content"]) for ms in messages]
        prompt = ChatPromptTemplate.from_messages(messages).format_prompt().to_string()
        res_generator = generate_chain.generate(prompt=prompt)
        res = ""
        for ans in res_generator: res = ans
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
        langfuse_context.update_current_observation(
            input=input_ms,
            output=res
        )
        return chat_completion

    @observe(name="Augmented Generate")
    def generator(question: str, docs: List[Document], history: List[Tuple[str, str]]):
        messages = augment_context(question, docs, history)
        chat_completion = llm_call(messages)
        langfuse_context.update_current_observation(
            input={"用户输入问题": question, "检索召回的文档": docs},
            output=chat_completion["choices"][0].message.content
        )
        return chat_completion["choices"][0].message.content

    @observe(name="Rag Pipeline Traceable")
    def chat_pipeline(question: str):
        retrieval_docs = retriever(question)
        result = generator(question, retrieval_docs, history)
        langfuse_context.update_current_observation(
            input={"用户输入问题": question},
            output=result
        )
        return result

    chat_pipeline(query)

    return BaseResponse(code=200, msg=f"Tracing success!")


