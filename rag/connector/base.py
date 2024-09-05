

from rag.common.configuration import settings
from rag.connector.utils import get_llm, get_embedding_model, get_vectorstore

embedding_model = get_embedding_model(settings.embeddings.model_name_or_path,
                                      settings.embeddings.model_engine)


llm_kwargs = {"grpc_port": settings.llm.grpc_port, "api_key": settings.llm.api_key}
llm = get_llm(model_name=settings.llm.model_name,
              model_engine=settings.llm.model_engine,
              ip=settings.llm.ip,
              port=settings.llm.port,
              **llm_kwargs)
