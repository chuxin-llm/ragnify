

from rag.common.configuration import settings
from rag.connector.utils import get_llm, get_embedding_model, get_vectorstore

embedding_model = get_embedding_model(settings.embeddings.model_name_or_path,
                                      settings.embeddings.model_engine)

llm_kwargs = {}
llm = get_llm(api_key=settings.llm.api_key,
              model_name=settings.llm.model_name,
              base_url=settings.llm.base_url,
              **llm_kwargs)

