
from .chinese_text_splitter import ChineseTextSplitter
from .chinese_recursive_text_splitter import ChineseRecursiveTextSplitter

from langchain_text_splitters import (
    LatexTextSplitter,
    MarkdownHeaderTextSplitter,
    MarkdownTextSplitter,
    NLTKTextSplitter,
    PythonCodeTextSplitter,
    RecursiveCharacterTextSplitter,
    SentenceTransformersTokenTextSplitter,
    SpacyTextSplitter
)

SPLITER_MAPPING = {
    "ChineseTextSplitter": ChineseTextSplitter,
    "ChineseRecursiveTextSplitter": ChineseRecursiveTextSplitter,
    "LatexTextSplitter": LatexTextSplitter,
    "MarkdownTextSplitter": MarkdownTextSplitter,
    "MarkdownHeaderTextSplitter": MarkdownHeaderTextSplitter,
    "PythonCodeTextSplitter": PythonCodeTextSplitter,
    "NLTKTextSplitter": NLTKTextSplitter,
    "RecursiveCharacterTextSplitter": RecursiveCharacterTextSplitter,
    "SentenceTransformersTokenTextSplitter": SentenceTransformersTokenTextSplitter,
    "SpacyTextSplitter": SpacyTextSplitter
}
