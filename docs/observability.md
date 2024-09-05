# 流程监控指南

RAGNIFY提供了对RAG应用全流程的监控接口，包含各个子模块的输入输出、每个计算流的耗时等，从而查看RAG应用全流程的监控信息。

## 前提条件

- 本接口基于LangFuse实现，需要提前[部署Langfuse](https://langfuse.com/docs/deployment/self-host)、创建`Projects`以及`公钥&私钥`。
- 根据[部署指南](docs%2Fdeployment.md)中选择的**配置参数**方法的不同，修改[/conf/config.yaml](../conf/config.yaml)或填写新建配置文件（.env格式）的`langchain`子项中的下列参数后，启动后端API服务。

  ```text
  langfuse_secret_key               # Langfuse平台项目的密钥
  langfuse_public_key               # Langfuse平台项目的公钥
  langfuse_host                     # Langfuse平台的访问地址
  ```


## 操作步骤

1. 调用RAG流程监控接口：`http://<host>:<port>/observability/trace_rag_pipeline`，接口描述详见**RAG流程监控接口**。

   其中，``<host>``和``<port>``为启动后端API服务时指定的主机地址和端口号。
   
2. 在浏览器中输入`langfuse_host`参数对应的值，进入创建的Project，即可看到所有的监控记录。
   

## 监控信息

本接口是对检索链（Retrieval Chain）和生成链（Generate Chain，即Augmented Generate）两个主流程及其子流程进行监控，包含每个流程的输入输出、流程执行时间等。

## RAG流程监控接口 

API的使用方法可参考[使用指南](service.md)中的**API使用概述**部分。

#### 接口介绍

当调用本接口时，系统会根据用户的输入，在指定的知识库中检索召回相关的文档，用于增强上下文并借助大模型生成答案。
过程中每个流程的输入输出、执行时间等信息都会上传到Langfuse平台。

#### 注意事项

- 知识库名称不为空，且不包含`/`字符
- 指定的知识库真实存在

#### 请求路径

`http://<host>:<port>/observability/trace_rag_pipeline`

其中：

- `<host>`：主机地址。

- `<port>`：RAGNIFY API服务的访问端口。

#### 请求参数

| 参数名称            | 类型                  | 必须 | 描述                |
| :------------------ | :-------------------- | :--- | :------------------ |
| query               | String                | 是   | 用户输入            |
| knowledge_base_name | String                | 是   | 知识库名称          |
| history             | List[Tuple[str, str]] | 否   | 对话历史 default=[] |

#### 请求示例

```python
import requests
import json

host = "<host>"
port = "<port>"
url = f"http://{host}:{port}/observability/trace_rag_pipeline"

payload = json.dumps({
  "query": "你好",
  "knowledge_base_name": "test_rag",
  "history": []
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

#### 返回参数

| 名称 | 类型 | 说明        |
| :--- | :--- | :---------- |
| code | int  | 响应码      |
| msg  | str  | API状态信息 |

#### 返回示例

```
{
  "code": 200,
  "msg": "Tracing success!"
}
```

#### HTTP状态码

| 状态码 | 说明                    |
|:----|:----------------------|
| 200 | 请求成功                  |
| 403 | 请求错误：包含预期外的字符或路径攻击关键字 |
| 404 | 请求错误：未找到知识库           |
