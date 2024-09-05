
import os
from typing import List, Dict
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from rag.connector.base import llm
from rag.connector.database.repository.knowledge_file_repository import list_files_from_db


def route_query_to_files(question, knowledge_base_name):

    exist_files = [os.path.basename(f) for f in list_files_from_db(knowledge_base_name)]
    double_check_keys = ["重庆"]

    prompt = PromptTemplate(
        template="""你是一个擅长将问题路由到文件的专家。\n
        已知有一个包含数据库中的所有文件名称的列表，请根据用户输入的问题，判断回答该问题需要使用哪个文件中的知识。\n
        判断的主要依据是问题中是否与文件名称有完全相同的关键词。\n
        注意如果文件名称中有明确的地域名称，那么只有当问题中出现完全相同的地域名称词才能将它们路由，“市级”不算地域名。\n
        注意你不需要将关键词返回，注意不需要做假设和解释，而是直接以JSON格式返回结果，并且以 "datasource"作为关键词给出路由的文件名称。\n
        若问题中的关键词在多个文件中都出现，请不要进行文件路由，请返回空JSON。 \n
        如果无法根据关键词判断问题应该和哪个文件路由，请返回空JSON。 \n
        下面是包含所有文件名称的列表: {file_list} \n
        需要路由的问题: {question}""",
        input_variables=["file_list", "question"]
    )

    question_router = prompt | llm | JsonOutputParser()
    res = question_router.invoke({"file_list": str(exist_files), "question": question})

    try:
        if isinstance(res, dict):
            file_name = res["datasource"]
            if file_name in exist_files:
                for key in double_check_keys:
                    if key in file_name and key not in question:
                        return []
                return [file_name]
        else:
            return []
    except Exception as e:
        return []

