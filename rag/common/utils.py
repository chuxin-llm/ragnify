
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from rag.common.configuration import settings
from langchain.docstore.document import Document


import nltk
nltk.data.path = [os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "nltk_data")] \
                + nltk.data.path


from typing import (
    List,
    Callable,
    Generator,
    Dict,
)


import logging
import logging.config
from logging.config import fileConfig
logging.config.fileConfig('./conf/log.cfg')

logger = logging.getLogger()


def run_in_thread_pool(
        func: Callable,
        params: List[Dict] = [],
) -> Generator:
    '''
    在线程池中批量运行任务，并将运行结果以生成器的形式返回。
    请确保任务中的所有操作是线程安全的，任务函数请全部使用关键字参数。
    '''
    tasks = []
    with ThreadPoolExecutor() as pool:
        for kwargs in params:
            thread = pool.submit(func, **kwargs)
            tasks.append(thread)

        for obj in as_completed(tasks):
            yield obj.result()


class DocumentWithVSId(Document):
    """
    矢量化后的文档
    """
    id: str = None
    score: float = 3.0


def get_prompt_template(type: str):
    if type == "rag":
        return settings.prompts.rag_template
    elif type == "chat":
        return settings.prompts.chat_template
    else:
        return ""

