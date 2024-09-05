
"""The definition of the rag configuration."""

import os
from functools import lru_cache
from rag.common.configuration_wizard import ConfigWizard, configclass, configfield


@configclass
class VectorStoreConfig(ConfigWizard):
    """Configuration class for the Vector Store connection.
    """

    type: str = configfield(
        "type",
        default="milvus",  # supports pgvector, milvus
        help_txt="The type of vector store",
    )

    name: str = configfield(
        "name",
        default="rag",
        help_txt="The name of vector store",
    )
    host: str = configfield(
        "host",
        default="",
        help_txt="The host of the machine running Vector Store DB",
    )
    port: str = configfield(
        "port",
        default="",
        help_txt="The port of the machine running Vector Store DB",
    )
    user: str = configfield(
        "user",
        default="",
        help_txt="The username of the machine running Vector Store DB",
    )
    password: str = configfield(
        "password",
        default="",
        help_txt="The password of the machine running Vector Store DB",
    )
    kwargs: dict = configfield(
        "kwargs",
        default="",
        help_txt="",
    )


@configclass
class LLMConfig(ConfigWizard):
    """Configuration class for the llm connection.
    """

    api_key: str = configfield(
        "api_key",
        default="",
        help_txt="OPENAI API kEY.",
    )
    ip: str = configfield(
        "ip",
        default="0.0.0.0",
        help_txt="The location of the Triton server hosting the llm model.",
    )
    port: str = configfield(
        "port",
        default="",
        help_txt="",
    )
    grpc_port: str = configfield(
        "grpc_port",
        default="",
        help_txt="",
    )
    model_name: str = configfield(
        "model_name",
        default="",
        help_txt="The name of the hosted model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="",
        help_txt="The server type of the hosted model",
    )


@configclass
class TextSplitterConfig(ConfigWizard):
    """Configuration class for the Text Splitter.

    :cvar chunk_size: Chunk size for text splitter. Tokens per chunk in token-based splitters.
    :cvar chunk_overlap: Text overlap in text splitter.
    """
    splitter_name: str = configfield(
        "splitter_name",
        default="ChineseTextSplitter",
        help_txt="Chunk size for text splitting.",
    )

    chunk_size: int = configfield(
        "chunk_size",
        default=510,
        help_txt="Chunk size for text splitting.",
    )
    chunk_overlap: int = configfield(
        "chunk_overlap",
        default=200,
        help_txt="Overlapping text length for splitting.",
    )

    smaller_chunk_size: int = configfield(
        "smaller_chunk_size",
        default=0,
        help_txt="",
    )

    summary: int = configfield(
        "summary",
        default=0,
        help_txt="",
    )


@configclass
class EmbeddingConfig(ConfigWizard):
    """Configuration class for the Embeddings.
    """

    model_name_or_path: str = configfield(
        "model_name_or_path",
        default="",
        help_txt="The name or local path of huggingface embedding model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="huggingface",
        help_txt="The server type of the hosted model. Allowed values are hugginface",
    )
    dimensions: int = configfield(
        "dimensions",
        default=1024,
        help_txt="The required dimensions of the embedding model. Currently utilized for vector DB indexing.",
    )

@configclass
class RerankConfig(ConfigWizard):
    """Configuration class for the Rerank Model.
    """
    model_name_or_path: str = configfield(
        "model_name_or_path",
        default="bge-reranker-large",
        help_txt="The model name or local path of rerank model.",
    )
    type: str = configfield(
        "type",
        default="rank",
        help_txt="The type of the rerank model. Allowed values are {rank, llm}",
    )


@configclass
class PromptsConfig(ConfigWizard):
    """Configuration class for the Prompts.

    :cvar chat_template: Prompt template for chat.
    :cvar rag_template: Prompt template for rag.
    """

    chat_template: str = configfield(
        "chat_template",
        default=(
            "<s>[INST] <<SYS>>"
            "你是一个乐于助人、尊重他人、诚实的助手。"
            "在安全的情况下，请尽可能提供帮助。"
            "请确保你的回答是积极的。"
            "<</SYS>>"
            "[/INST] {context} </s><s>[INST] {query} [/INST]"
        ),
        help_txt="Prompt template for chat.",
    )
    rag_template: str = configfield(
        "rag_template",
        default=(
            "<s>[INST] <<SYS>>"
            "根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，"
            "请说 “根据已知信息无法回答该问题”，不允许在答案中添加编造成分，答案请使用中文。"
            "<</SYS>>"
            "<s>[INST] 已知信息：{context} 问题：{query} 答案：[/INST]"
        ),
        help_txt="Prompt template for rag.",
    )


@configclass
class ServerConfig(ConfigWizard):

    api_server_host: str = configfield(
        "api_server_host",
        default="127.0.0.1",
        help_txt="Api Server host",
    )

    api_server_port: int = configfield(
        "api_server_port",
        default=7861,
        help_txt="Api Server port",
    )

    web_server_port: int = configfield(
        "web_server_port",
        default=9003,
        help_txt="Web Server port",
    )


@configclass
class LangfuseConfig(ConfigWizard):

    langfuse_secret_key: str = configfield(
        "langfuse_secret_key",
        default="",
        help_txt=".",
    )

    langfuse_public_key: str = configfield(
        "langfuse_public_key",
        default="",
        help_txt=".",
    )

    langfuse_host: str = configfield(
        "langfuse_host",
        default="",
        help_txt=".",
    )


@configclass
class KnowledgeGraphConfig(ConfigWizard):

    type: str = configfield(
        "type",
        default="",
        help_txt="The type of the Graph DB",
    )
    ip: str = configfield(
        "ip",
        default="",
        help_txt="The ip of the Graph DB",
    )
    port: str = configfield(
        "port",
        default="",
        help_txt="The port of the Graph DB",
    )
    username: str = configfield(
        "username",
        default="",
        help_txt="The username of the Graph DB",
    )
    password: str = configfield(
        "password",
        default="",
        help_txt="The password of the Graph DB",
    )
    gql_generation_template: str = configfield(
        "gql_generation_template",
        default="",
        help_txt="",
    )
    kwargs: dict = configfield(
        "kwargs",
        default="",
        help_txt="",
    )


@configclass
class RagConfig(ConfigWizard):
    """Configuration class for the application.

    :cvar vector_store: The configuration of the vector db connection.
    :type vector_store: VectorStoreConfig
    :cvar llm: The configuration of the backend llm server.
    :type llm: LLMConfig
    :cvar text_splitter: The configuration for text splitter
    :type text_splitter: TextSplitterConfig
    :cvar embeddings: The configuration for huggingface embeddings
    :type embeddings: EmbeddingConfig
    :cvar prompts: The Prompts template for RAG and Chat
    :type prompts: PromptsConfig
    """

    vector_store: VectorStoreConfig = configfield(
        "vector_store",
        env=False,
        help_txt="The configuration of the vector db connection.",
        default=VectorStoreConfig(),
    )
    llm: LLMConfig = configfield(
        "llm",
        env=False,
        help_txt="The configuration for the server hosting the Large Language Models.",
        default=LLMConfig(),
    )
    text_splitter: TextSplitterConfig = configfield(
        "text_splitter",
        env=False,
        help_txt="The configuration for text splitter.",
        default=TextSplitterConfig(),
    )
    embeddings: EmbeddingConfig = configfield(
        "embeddings",
        env=False,
        help_txt="The configuration of embedding model.",
        default=EmbeddingConfig(),
    )
    reranker: RerankConfig = configfield(
        "reranker",
        env=False,
        help_txt="The configuration of rerank model.",
        default=RerankConfig(),
    )
    prompts: PromptsConfig = configfield(
        "prompts",
        env=False,
        help_txt="Prompt templates for chat and rag.",
        default=PromptsConfig(),
    )
    server: ServerConfig = configfield(
        "server",
        env=False,
        help_txt="Server args.",
        default=ServerConfig(),
    )
    langfuse: LangfuseConfig = configfield(
        "langfuse",
        env=False,
        help_txt="",
        default=LangfuseConfig(),
    )
    knowledge_graph: KnowledgeGraphConfig = configfield(
        "knowledge_graph",
        env=False,
        help_txt="The configuration of the graph db.",
        default=KnowledgeGraphConfig(),
    )


@lru_cache
def get_config() -> "ConfigWizard":
    """Parse the application configuration."""
    config = RagConfig.from_file(os.getcwd() + "/conf/config.yaml")
    if config:
        return config
    raise RuntimeError("Unable to find configuration.")


settings = get_config()
