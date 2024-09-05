# 度量指标评估指南
度量指标评估对于RAG至关重要，通过度量指标评估可以感知并逐步提升RAG检索的信息以及生成内容的准确性和相关性。

[Ragas](https://github.com/explodinggradients/ragas)是一个开源的度量指标评估工具。RAGNIFY提供了基于Ragas的评估脚本，用于快速执行度量指标评估。

度量指标评估分为两个步骤：

1. 准备评估数据：提前准备问答数据，使用脚本生成待评估数据。
2. 执行评估：使用评估脚本，基于Ragas进行评估。

## 1 准备待评估数据
执行评估前，需要准备待评估的数据，包含以下信息：

| 参数      | 说明                                             |
| -------- | ------------------------------------------------ |
| filename | 知识库文件名称，应预先给出。                     |
| question | 需要评测的问题，应预先给出。                     |
| gt_answer | 正确答案，应预先给出。                           |
| context  | 执行本章节脚本后，会得到的基于question的上下文。 |
| answer   | 执行本章节脚本后，会得到的基于question的答案。   |

**前提条件**

已按照[部署指南](deployment.md)启动了RAGNIFY服务。

**操作步骤**

1. 创建Json文件，包含``filename``、``question``和``gt_answer``，格式如下：

   ```text
   [
       {
           "filename": "常见疾病知识大全.txt", 
           "question": "流行感冒怎么预防？", 
           "gt_answer": "防止流行感冒的方法包括避免吸入有害物质和过敏原，提高呼吸道的抵抗力。在气候变化和寒冷季节时，应注意及时添减衣服，避免受凉感冒。同时，加强体育锻炼来提高身体素质，注意观察病情变化，掌握发病规律，以便事先采取措施。"
       }
   ]
   ```

3. 执行以下命令，根据步骤1的Json文件，生成包含所有待评估数据的Json文件。

   ```shell
   python tools/evaluate/format_evaluate_data.py --ip <ip> --port <port> --knowledge_base_name <knowledge_base_name> \
         --org_file_path <org_file_path> --dump_file_path <dump_file_path>
   ```

   其中：

   - `<ip> `：后端API服务的访问IP。

   - `<port> `：后端API服务的访问端口。

   - `<knowledge_base_name>`：需要评估的知识库文件名称。

   - `<org_file_path> `：原始Json文件路径，即上述步骤2中提前准备的文件。
   
   - `<dump_file_path>`：脚本生成的待评估数据Json文件保存路径。

## 2 执行评估

根据接入大模型推理服务的不同方式，使用评估脚本：run_ragas_evaluate.py，快速执行Ragas评估。

- 方式一：部署在NVIDIA GPU卡上的OpenAI Compatible Server
- 方式二：OpenAI在线推理服务

### 方式一：部署在NVIDIA GPU卡上的OpenAI Compatible Server

执行以下命令，执行评估：

```shell
python tools/evaluate/run_ragas_evaluate.py --llm_server_ip <LLM_SERVER_IP> --llm_server_port <LLM_SERVER_PORT> \
      --llm_model_name <LLM_MODEL_NAME> --llm_model_engine nvidia \
       --embedding_model_name_or_path <EMBEDDINGS_MODEL_NAME_OR_PATH> --embedding_model_engine huggingface  \
       --eval_file_path <EVAL_FILE_PATH> 
```

其中：

- `<LLM_SERVER_IP>`：大模型推理服务IP。
- `<LLM_SERVER_PORT>`：大模型推理服务端口。
- `<LLM_MODEL_NAME>`：大模型名称。
- `<EMBEDDINGS_MODEL_NAME_OR_PATH>`： Embedding模型参数路径。
- `<EVAL_FILE_PATH>`：待评估数据Json文件保存路径，即**准备待评估数据**中的`<dump_file_path>`，例如：`tools/evaluate/eval_file.json`。


### 方式二：OpenAI在线推理服务

执行以下命令，执行评估：

```shell
OPENAI_API_KEY = <API_KEY>
python tools/evaluate/run_ragas_evaluate.py --eval_file_path <EVAL_FILE_PATH> --openai_api_key $OPENAI_API_KEY
```

其中：

- `<API_KEY>`：OpenAI API密钥。

- `<EVAL_FILE_PATH>`：待评估数据Json文件保存路径，即**准备待评估数据**中的`<dump_file_path>`，例如：`tools/evaluate/eval_file.json`。
