from dataclasses import dataclass
from typing import List, Tuple, Union
from langchain_core.documents import Document

from rag.chains.base import BaseGenerationChain

from rag.common.utils import get_prompt_template
from langchain_core.messages.chat import ChatMessage
from langchain_core.language_models import LLM, BaseChatModel

from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate


@dataclass
class GenerateChain(BaseGenerationChain):
    llm: Union[LLM, BaseChatModel]
    stream: bool = False

    def augment(self, query: str,
                docs: List[Document]):
        context = "\n".join([doc.page_content for doc in docs])

        prompt_template = get_prompt_template(type="rag")
        context = PromptTemplate.from_template(prompt_template).format(query=query, context=context)
        return context

    def generate(self, prompt):
        if self.stream:
            result = ""
            for res in self.llm.stream(prompt):
                result += res.content if isinstance(self.llm, BaseChatModel) else res
                yield result
        else:
            result = self.llm.invoke(prompt)
            result = result.content if isinstance(self.llm, BaseChatModel) else result
            for res in iter([result]):
                yield res

    def chain(self,
              query: str,
              docs: List[Document],
              history: List[Tuple[str, str]]):
        message_list = [ChatMessage(role=h[0], content=h[1]) for h in history]
        prompt = ChatPromptTemplate.from_messages(
            message_list + [ChatMessage(role="user", content=self.augment(query, docs))]).format_prompt().to_string()
        return self.generate(prompt)

