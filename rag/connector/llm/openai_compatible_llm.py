
from typing import List, Any, Optional

from openai import OpenAI
from langchain_core.language_models import LLM
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import GenerationChunk

from rag.common.utils import logger


class OpenaiCompatibleLLM(LLM):

    model_name: str
    api_key: str
    base_url: str
    output_len: int = 1024

    def _stream(self,
                prompt: str,
                stop: Optional[List[str]] = None,
                run_manager: Optional[CallbackManagerForLLMRun] = None,
                **kwargs: Any, ):
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                stream=True
            )

        except Exception as e:
            msg = f'inference request error'
            logger.error(f'{e.__class__.__name__}: {msg}', exc_info=e)
            return ''

        for res in response:
            token = res.choices[0].delta.content
            if token: yield GenerationChunk(text=token)

    def _call(self,
              prompt: str,
              stop: Optional[List[str]] = None,
              run_manager: Optional[CallbackManagerForLLMRun] = None,
              **kwargs: Any, ):
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
        except Exception as e:
            msg = f'inference request error'
            logger.error(f'{e.__class__.__name__}: {msg}', exc_info=e)
            return ''

        return response.choices[0].message.content

    def _llm_type(self) -> str:
        """Return type of chat model."""
        return self.model_name
