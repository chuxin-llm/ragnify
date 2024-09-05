
from langchain_core.prompts.prompt import PromptTemplate
from rag.connector.base import llm

# Default prompt
DEFAULT_QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""你是一位优秀的AI助手，你的任务是更具给定的用户问题，生成三个不同版本的问题表达，以便从向量数据库中检索相关文档。通过从多个角度生成问题，你的目标是帮助用户克服基于距离的相似性搜索的一些局限性。
    请直接给出答案，并用换行符分隔生成的问题。原始用户问题: {question}""",
)


def generate_queries(question: str):
    prompt = DEFAULT_QUERY_PROMPT.format(question=question)
    response = llm.invoke(prompt)
    return response.strip().split("\n")
