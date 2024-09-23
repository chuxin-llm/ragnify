# 参数说明

## 1 vector_store

向量数据库支持配置的参数如下：

| 参数名称 | 类型 | 默认值                   | 环境变量名称              | 是否需要自定义 | 说明                                                         |
| :------- | :--- | :----------------------- | :------------------------ | :------------- | :----------------------------------------------------------- |
| type     | str  | milvus                   | APP_VECTOR_STORE_TYPE     | -              | 向量数据库类型，可选项：milvus。                             |
| name     | str  | rag                      | APP_VECTOR_STORE_NAME     | -              | 向量数据库/知识库名称。                                      |
| host     | str  | -                        | APP_VECTOR_STORE_HOST     | ✅              | 向量数据库ip地址。                                           |
| port     | str  | -                        | APP_VECTOR_STORE_PORT     | ✅              | 向量数据库连接端口。                                         |
| user     | str  | -                        | APP_VECTOR_STORE_USER     | -              | 向量数据库连接用户名。                                       |
| password | str  | -                        | APP_VECTOR_STORE_PASSWORD | -              | 向量数据库连接密码。                                         |
| kwargs   | str  | 见**向量数据库配置信息** | APP_VECTOR_STORE_KWARGS   | -              | 向量数据库配置信息，兼容不同类型数据库需求。当前仅支持默认值。 |

#### 向量数据库配置信息

默认值如下：

```
{
      "search_params":{"metric_type": "IP"},
      "index_params":{"metric_type": "IP", "index_type":"HNSW", "params": {"M": 8, "efConstruction": 64}}
  }
```

## 2 llm

大模型推理服务支持配置的参数如下：

| 参数名称         | 类型 | 默认值    | 环境变量名称               | 是否需要自定义 | 说明                |
|:-------------| :--- |:-------|:---------------------| :------------- |:------------------|
| api_key      | str  | -      | APP_LLM_API_KEY      | -              | 大模型推理服务 apikey。   |
| base_url     | str  | -      | APP_LLM_BASE_URL     | ✅              | 大模型推理服务 base_url。 |
| model_name   | str  | -      | APP_LLM_MODEL_NAME   | ✅              | 大模型名称。            |

## 3 text_splitter

文档分词器支持配置的参数如下：

| 参数名称           | 类型 | 默认值              | 环境变量名称                               | 是否需要自定义 | 说明                                                         |
| :----------------- | :--- | :------------------ |:-------------------------------------| :------------- | :----------------------------------------------------------- |
| splitter_name      | str  | ChineseTextSplitter | APP_TEXT_SPLITTER_SPLITTER_NAME      | -              | 配置解析文本时使用的分词器名称。<br>支持Langchain分词器或自定义分词器，详见**支持的分词器**。<br>若配置的分词器暂不支持，默认选择ChineseTextSplitter。 |
| chunk_size         | int  | 510                 | APP_TEXT_SPLITTER_CHUNK_SIZE         | -              | chunk窗口大小。                                              |
| chunk_overlap      | int  | 200                 | APP_TEXT_SPLITTER_CHUNK_OVERLAP      | -              | chunk滑动窗口冗余长度。                                      |
| smaller_chunk_size | int  | 0                   | APP_TEXT_SPLITTER_SMALLER_CHUNK_SIZE | -              | 是否开启small-to-big优化，详见**MultiVector优化**：<br> **0**：不开启<br> **大于0的整数**：开启 |
| summary            | str  | 0                   | APP_TEXT_SPLITTER_SUMMARY            | -              | 是否开启summary优化，详见**MultiVector优化**：<br> **0**：不开启<br> **1**：开启 |

### 支持的分词器

已兼容的[Langchain分词器](https://github.com/langchain-ai/langchain/blob/master/libs/text-splitters/README.md)：

- CharacterTextSplitter
- LatexTextSplitter
- MarkdownHeaderTextSplitter
- MarkdownTextSplitter
- NLTKTextSplitter
- PythonCodeTextSplitter
- RecursiveCharacterTextSplitter
- SentenceTransformersTokenTextSplitter
- SpacyTextSplitter

自定义分词器：

- ChineseTextSplitter

自定义方法详见[开发指南](development.md)。

### MultiVector优化

在文档索引过程中，越短的文档片段（chunk）越能清晰地表达文本语义。MultiVector优化是通过对较大的chunk进行分段并形成多个更精准语义表达的一系列方法。进行MultiVector优化后，可以提升检索召回的准确性和完整性，但是会消耗更多的存储和计算资源。

RAGNIFY支持两个优化方法：

- **small-to-big** ：通过`smaller_chunk_size`参数配置。会消耗更多的存储资源。
- **summary** ： 通过`summary`参数配置。会消耗更多的计算资源。

#### small-to-big

将`smaller_chunk_size`设置为大于0的整数即可开启该优化方法，可以将切分好的chunk进一步切分为更小的chunk。
在索引构建阶段，使用更小的chunk进行向量化，但在检索阶段召回的文档是原chunk。

#### summary

将`summary`设置为1即可开启该优化方法，可以通过大模型为切分好的chunk生成一个摘要。

在索引构建阶段，对摘要进行向量化，但在检索阶段召回的文档是原chunk。

## 4 embeddings

Embedding模型用于将文本向量化，支持配置的参数如下：

| 参数名称               | 类型  | 默认值         | 环境变量名称                            | 是否需要自定义 | 说明                                                                                                     |
|:-------------------|:----|:------------|:----------------------------------| :------------- |:-------------------------------------------------------------------------------------------------------|
| model_name_or_path | str | -           | APP_EMBEDDINGS_MODEL_NAME_OR_PATH | ✅              | 模型名称或模型的本地存储路径。<br>**推荐**提前下载模型并填写模型的本地存储路径，填写格式参见**本地存储路径格式**。模型下载方法参见**下载模型**。<br/>如果未提前下载模型，填写模型名称。 |
| model_engine       | str | huggingface | APP_EMBEDDINGS_MODEL_ENGINE       | -              | 加载模型的backend。当前仅支持huggingface作为模型加载源。                                                                  |
| device             | str | cuda:0      | APP_EMBEDDINGS_DEVICE             | -              | 指定加载模型的设备                                                                                     |


### 下载模型
**强烈推荐您试用我们自研的[Chuxin-Embedding](https://huggingface.co/chuxin-llm/Chuxin-Embedding)模型**

您也可以选择下载其它主流的开源模型，例如：

| 模型名称              | 语言 | 模型链接                                                     |
| :-------------------- | :--- | :----------------------------------------------------------- |
| bge-large-zh          | 中文 | [HF国内站（推荐）](https://hf-mirror.com/BAAI/bge-large-zh)  |
| bce-embedding-base_v1 | 中英 | [HF国内站（推荐）](https://hf-mirror.com/maidalun1020/bce-embedding-base_v1) |


#### 下载步骤

**说明**：如果下载Rerank模型时已执行了步骤1和步骤2，则可直接执行步骤3，下载Embedding模型。

1. 执行以下命令，安装依赖：

   ```shell
   pip install -U huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. 根据不同的操作系统，设置环境变量：

   - 执行以下命令，在Linux或MacOS上设置环境变量：

     ```shell
     export HF_ENDPOINT=https://hf-mirror.com
     ```

   - 执行以下命令，在Windows上设置环境变量：

     ```shell
     $env:HF_ENDPOINT = "https://hf-mirror.com"
     ```

3. 执行以下命令，下载模型：

   ```shell
   huggingface-cli download --resume-download <hf_model_name> --local-dir <local_model_dir> --local-dir-use-symlinks False
   ```

   其中：

   - ``<hf_model_name>``：HF站上的模型名称，例如：chuxin-llm/Chuxin-Embedding。
   
   - ``<local_model_dir>``：模型的本地存储路径。

### 本地存储路径格式

- 配置文件[/conf/config.yaml](../conf/config.yaml)中的路径格式：本地存储路径的绝对地址，例如：`/Users/administrator/Documents/projects/models/bge-large-zh`。
- 新建配置文件（后缀为.env）中的路径格式：本地存储路径的相对地址，``/models/xxxx``形式，即以``/models``为起始的路径，例如：`/models/bge-embedding-zh`。

## 5 reranker

Rerank模型用于对检索模块中的召回文档进行重排序，支持配置的参数如下：

| 参数名称           | 类型 | 默认值 | 环境变量名称                    | 是否需要自定义 | 说明                                                         |
| :----------------- | :--- | :----- | :------------------------------ | :------------- | :----------------------------------------------------------- |
| model_name_or_path | str  | -      | APP_RERANKER_MODEL_NAME_OR_PATH | ✅              | 模型名称或模型的本地存储路径。<br/>**推荐**提前下载模型并填写模型存储的本地地址，填写格式参见**本地存储路径格式**。模型下载方法参见**下载模型**。<br/>如果未提前下载模型，填写模型名称。 |
| type               | str  | rank   | APP_RERANKER_TYPE               | -              | Rerank模型的类型，仅支持rank类型的Rerank模型。               |
| device             | str | cuda:0      | APP_RERANKER_DEVICE             | -              | 指定加载模型的设备                                                                                     |

### 下载模型

您可以根据实际情况，选择列表中的一个模型进行下载：

| 模型名称             | 语言 | 模型链接                                                     |
| :------------------- | :--- | :----------------------------------------------------------- |
| bge-reranker-large   | 中文 | [HF国内站（推荐）](https://hf-mirror.com/BAAI/bge-reranker-large) |
| bce-reranker-base_v1 | 中英 | [HF国内站（推荐）](https://hf-mirror.com/maidalun1020/bce-reranker-base_v1) |

#### 下载步骤

**说明**：如果下载Embedding模型时已执行了步骤1和步骤2，则可直接执行步骤3，下载Rerank模型。

1. 执行以下命令，安装依赖：

   ```shell
   pip install -U huggingface_hub -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. 根据不同的操作系统，设置环境变量：

   - 执行以下命令，在Linux或MacOS上设置环境变量：

     ```shell
     export HF_ENDPOINT=https://hf-mirror.com
     ```

   - 执行以下命令，在Windows上设置环境变量：

     ```shell
     $env:HF_ENDPOINT = "https://hf-mirror.com"
     ```

3. 执行以下命令，下载模型：

   ```shell
   huggingface-cli download --resume-download <hf_model_name> --local-dir <local_model_dir> --local-dir-use-symlinks False
   ```

   其中：

   - ``<hf_model_name>``：HF站上的模型名称，例如：BAAI/bge-reranker-large。
   
   - ``<local_model_dir>``：模型的本地存储路径。

### 本地存储路径格式

- 配置文件[/conf/config.yaml](../conf/config.yaml)中的路径格式：存储路径的绝对地址，例如：`/Users/administrator/Documents/projects/models/bge-reranker-large`。
- 新建配置文件（后缀为.env）中的路径格式：存储路径的相对地址，``/models/xxxx``形式，即以``/models``为起始的路径，例如：`/models/bge-reranker-large`。

## 6 prompts

RAGNIFY支持用户自定义知识库对话模板，使模型生成更加准确和相关的输出结果。

| 参数名称     | 类型 | 默认值 | 环境变量名称              |是否需要自定义 | 说明                                            |
| :----------- | :--- | :----- | :----------------------- |:------------- | :--------------------- |
| rag_template | str  | 见下文     | APP_PROMPTS_RAG_TEMPLATE |✅              |知识库对话模板，用于增强输入大模型的上下文。  |

默认的知识库对话模板：

```python 
rag_template = "<s>[INST] <<SYS>>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，不允许在答案中添加编造成分，答案请使用中文。<</SYS>><s>[INST] 已知信息：{context} 问题：{query} 答案：[/INST]"
```

## 7 langfuse

RAGNIFY基于LangFuse提供了对RAG应用全流程的监控接口，包含各个子模块的输入输出、每个计算流的耗时等。以下参数适用于流程监控，见[流程监控指南](observability.md)。

| 参数名称             | 类型 | 默认值 | 环境变量名称                  | 是否需要自定义 | 说明               |
| :------------------- | :--- |:----|:------------------------|:--------|:-----------------|
| langfuse_secret_key    | str  | -   | APP_LANGFUSE_LANGFUSE_SECRET_KEY | -       | Langfuse平台项目的密钥。 |
| langfuse_public_key    | str  | -   | APP_LANGFUSE_LANGFUSE_PUBLIC_KEY | -       | Langfuse平台项目的公钥。 |
| langfuse_host   | str  | -   | APP_LANGFUSE_LANGFUSE_HOST       | -       | Langfuse平台的访问地址。 |


## 8 server

启动API服务的相关参数

| 参数名称             | 类型 | 默认值     | 环境变量名称                  | 是否需要自定义 | 说明               |
| :------------------- | :--- |:--------|:------------------------|:--------|:-----------------|
| api_server_host    | str  | 0.0.0.0 | APP_SERVER_API_SERVER_HOST | -       | Api Server Host。 |
| api_server_port    | str  | 7861    | APP_SERVER_API_SERVER_PORT | -       | Api Server端口号。   |
| web_server_port   | str  | 9003    | APP_SERVER_WEB_SERVER_PORT       | -       | WebUI端口号。        |


