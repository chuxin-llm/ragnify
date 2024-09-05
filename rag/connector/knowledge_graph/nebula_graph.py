
from typing import List

from rag.common.configuration import settings
from rag.common.utils import logger
from rag.connector.knowledge_graph.base import KnowledgeGraph

from langchain_core.prompts import BasePromptTemplate
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.documents import Document
from langchain_core.language_models import BaseLanguageModel, BaseChatModel
from langchain_community.graphs.nebula_graph import NebulaGraph, rel_query


NGQL_GENERATION_TEMPLATE = """<指令> 你是一位出色的AI助手，擅长将用户的问题转化成图数据库查询语句。
现在你的任务是根据用户输入的问题，生成nGQL命令，用于查询NebulaGraph图数据库。
只能使用提供的图数据节点、关系类型和属性信息，不允许使用除此之外的其它信息。</指令>
图结构: {schema} 

注意事项: 不要在回复中包含任何解释和抱歉信息。除了构建nGQL命令之外，请勿回答任何可能提出其他问题的问题。除了生成的nGQL命令外，请勿包含任何文本。

问题: {question}
nGQL命令: """


NGQL_GENERATION_PROMPT = PromptTemplate(
    template=NGQL_GENERATION_TEMPLATE, input_variables=["schema", "question"]
)


# TRIPLE_GENERATION_TEMPLATE = """<指令> 你是一位出色的AI助手。
# 现在你的任务是根据查询NebulaGraph图数据库的查询命令以及查询结果，结构化出对应的图结构知识三元组，返回结果请以列表形式返回。
# 只能使用查询指令和查询结果中提供的节点、关系和属性信息，不允许使用除此之外的其它信息。</指令>
# <注意事项> 不要在回复中包含任何解释和抱歉信息。除了给出知识三元组列表之外，请勿回答任何可能提出其他问题的问题。除了生成的知识三元组列表外，请勿包含任何文本。</注意事项>
#
# <示例1：
# 查询指令: {sql}
# 查询结果: {result}
# </示例1>
#
# <示例2：
# 查询指令: {sql}
# 查询结果: {result}
# </示例2>
#
# 开始任务!
#
# 图结构: {schema}
# 查询指令: {sql}
# 查询结果: """
#
#
# TRIPLE_GENERATION_PROMPT = PromptTemplate(
#     template=TRIPLE_GENERATION_TEMPLATE, input_variables=["schema", "sql"]
# )


CONTEXT_TEMPLATE = """下面是根据您的问题，在图数据库中查询得到的相关信息：

问题: {question}
查询结果: {context}"""
CONTEXT_PROMPT = PromptTemplate(
    template=CONTEXT_TEMPLATE, input_variables=["question", "context"]
)


class NebulaKnowledgeGraph(KnowledgeGraph):

    def __init__(self,
                 llm: BaseLanguageModel,
                 ngql_prompt: BasePromptTemplate = NGQL_GENERATION_PROMPT,
                 context_prompt: BasePromptTemplate = CONTEXT_PROMPT):
        self.llm = llm
        self.ngql_prompt = ngql_prompt
        self.context_prompt = context_prompt

        self.graph = self._init_graph()
        self.graph_schema = self.get_schema()

    def _init_graph(self):
        kwargs = settings.knowledge_graph.kwargs
        ip = settings.knowledge_graph.ip
        port = settings.knowledge_graph.port
        username = settings.knowledge_graph.username
        password = settings.knowledge_graph.password
        return NebulaGraph(username=username,
                           password=password,
                           address=ip,
                           port=port,
                           **kwargs)

    def get_schema(self):

        tags_schema, edge_types_schema, relationships = [], [], []
        for tag in self.graph.execute("SHOW TAGS").column_values("Name"):
            tag_name = tag.cast()
            tag_schema = {"tag": tag_name, "properties": []}
            r = self.graph.execute(f"DESCRIBE TAG `{tag_name}`")
            props, types, comments = r.column_values("Field"), r.column_values("Type"), r.column_values("Comment")
            for i in range(r.row_size()):
                tag_schema["properties"].append((props[i].cast(), types[i].cast(), comments[i].cast()))
            tags_schema.append(tag_schema)
        for edge_type in self.graph.execute("SHOW EDGES").column_values("Name"):
            edge_type_name = edge_type.cast()
            edge_schema = {"edge": edge_type_name, "properties": []}
            r = self.graph.execute(f"DESCRIBE EDGE `{edge_type_name}`")
            props, types, comments = r.column_values("Field"), r.column_values("Type"), r.column_values("Comment")
            for i in range(r.row_size()):
                edge_schema["properties"].append((props[i].cast(), types[i].cast()))
            edge_types_schema.append(edge_schema)

            # build relationships types
            r = self.graph.execute(
                rel_query.substitute(edge_type=edge_type_name)
            ).column_values("rels")
            if len(r) > 0:
                relationships.append(r[0].cast())

        return (
            f"Node properties: {tags_schema}\n"
            f"Edge properties: {edge_types_schema}\n"
            f"Relationships: {relationships}\n"
        )

    def generate_ngql(self, question):
        prompt = self.ngql_prompt.format(schema=self.graph_schema, question=question)
        res = self.llm.invoke(prompt)
        return res.content if isinstance(self.llm, BaseChatModel) else res

    def call(self, question) -> List[Document]:

        # step 1. 根据问题和graph schema生成查询命令
        generated_ngql = self.generate_ngql(question)

        # step 2. 执行查询命令
        response = {}
        try:
            response = self.graph.query(generated_ngql)
        except Exception as e:
            msg = f"执行查询命令{generated_ngql}失败：{e}"
            logger.error(f'{e.__class__.__name__}: {msg}', exc_info=e)

        # step 3. 生成document
        if response:
            content = self.context_prompt.format(question=question, context=str(response))
            return [Document(page_content=content)]
        else:
            return []


if __name__ == '__main__':

    from langchain_openai.chat_models import ChatOpenAI
    openai_api_key = "sk-....."
    llm = ChatOpenAI(
        model_name="gpt-4",
        openai_api_key=openai_api_key
    )

    nebula_graph = NebulaKnowledgeGraph(llm)

    question = "病毒性肠炎的预防措施有哪些？"
    nebula_graph.call(question)






