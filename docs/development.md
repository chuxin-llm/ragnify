# 开发指南

## 1. Fork仓库
将Repo Fork到开发者的个人空间，单击仓库页面右上方的**Fork**按钮即可。
接着`cd `切换目录后，您就可以在自己的个人代码仓库中开发具体的功能了。

## 2. 功能开发

您可以参考开发规范进行模块开发。

### 2.1 开发规范

功能开发之前，请从以下方面熟悉本项目的开发规范。

- 目录规范
- 代码注释
- 编程规范
- 文档更新

#### 目录规范

```text
- APP-META
    |- bin
        |- start.sh                                     # RAG系统启动脚本
    |- etc
    |- Dockerfile                                       # 镜像制作脚本文件
- conf 
    |- config.yaml                                      # RAG系统配置文件
    |- log.cfg                                          # 日志配置文件
- docs                                                  # 文档目录
- examples                                              # 场景化应用示例
- imgs
- nltk_data
- rag                                                   # RAG框架核心代码
    |- chains                                           # RAG框架中三个基本流程（Chains）的定义与实现
    |- common                                           # 框架通用脚本
    |- connector                                        # RAG依赖服务连接器：大模型推理、embedding、向量数据库...
    |- module                                           # RAG框架中功能组件的定义与实现
- server                                                # RAG架构服务层定义与实现
- tools                                                 # RAG生态工具：评估工具 & 流程监控工具
- build.sh                                              # docker镜像构建脚本
- setup.py                                              # 应用打包脚本
- start.py                                              # 一键部署脚本
- LICENSE                                               # 开源协议
```


#### 代码注释

对于代码中重要的部分，需要加入注释介绍功能，帮助使用者快速熟悉框架代码结构，包括但不仅限于：

- 函数的功能说明，例如：负责加载pdf文档，返回Document对象。
- 功能模块和优化策略的实现方法或引用信息：

```text
Perform weighted Reciprocal Rank Fusion on multiple rank lists.
     You can find more details about RRF here:
     https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
```

- 系统运行过程中的关键状态或特殊情况说明，例如：打印（print）、服务出错等。


#### 编程规范

Python代码遵循[PEP8](https://gitee.com/link?target=https%3A%2F%2Fpeps.python.org%2Fpep-0008%2F)规范。

#### 文档更新

在进行开发之前，强烈建议先熟悉本项目的所有文档，系统地了解RAGNIFY关于部署、使用、参数配置等方面的流程和方法，可以有效避免很多问题。若您所开发内容涉及到本项目中的文档内容，请务必将文档一并修改，并在提交PR时备注文档修改的位置和内容。

例如：

您贡献的新功能模块或流程方案需要新增参数配置项，请确认该参数已支持在`/conf/config.yaml`中进行配置，并将该参数信息更新到[参数说明](configuration.md)文档中。

### 2.2 模块开发

RAGNIFY是以大模型为核心的知识问答框架，开发者可以对RAG计算流程、模块实现、组件接入等多个方面进行优化和开发，但请保证RAG算法计算流程仍符合框架设计：

- 三个主流程链（Chains）是RAG后端对接系统服务的通道，不可删除或改变其[基类定义](../rag/chains/base.py)，但可以优化每个计算流程的实现方案。
- 流程链可进一步细化拆解为六个模块，请贡献者准确判断待开发功能属于其中的哪一个模块，并将脚本新建在该模块下。例如“加载文档”和“切分文档”是索引构建（知识库构建）流程中的重要环节，所以将[loader](../rag/module/indexing/loader)和[splitter](../rag/module/indexing/splitter)放在[indexing](../rag/module/indexing)目录下。

为了支持用户在具体应用场景中的特殊数据加载和文档切分需求，RAGNIFY允许用户自定义开发文档加载器和分词器，并将其配置到系统中。

#### 开发文档加载器

1. 在`rag/module/indexing/loader`目录下新建一个文件，用于开发新的加载器类，例如`my_new_loader.py`。开发过程具体可参考[pdf_loader.py](..%2Frag%2Fmodule%2Findexing%2Floader%2Fpdf_loader.py)。

   **注意**：加载器类类名必须包含`Customized`，例如``MyNewCustomizedLoader``。
2. 修改 [\_\_init__.py](..%2Frag%2Fmodule%2Findexing%2Floader%2F__init__.py)文件，将开发的加载器类添加在`LOADER_MAPPING`中，用于指定加载哪些文件类型。

```python
LOADER_MAPPING = {
    "CustomizedOcrPdfLoader": [".pdf"],
    "CustomizedOcrDocLoader": [".docx", ".doc"],
    "MyNewCustomizedLoader": [".txt"]
}
```

#### 开发分词器

1. 在`rag/module/indexing/splitter`目录下新建一个文件，用于开发新的分词器类，例如`my_new_splitter.py`。开发过程具体可参考[chinese_text_splitter.py](..%2Frag%2Fmodule%2Findexing%2Fsplitter%2Fchinese_text_splitter.py)。
2. 修改[\_\_init__.py](..%2Frag%2Fmodule%2Findexing%2Fsplitter%2F__init__.py)文件，将开发的分词器类添加到`SPLITER_MAPPING`中，即指定开发的分词器。

## 3. 功能自测
完成代码开发和文档更新后需要完成功能自测。

1. 首先请参考[部署指南](docs/deployment.md)和[参数配置](docs/configuration.md)文档，基于本项目部署本地知识问答系统。请确保您开发的模块成功注入系统的计算流程。
2. 根据[使用指南](/docs/service.md)，测试知识问答能力是否可用。若服务可调用但大模型回答的内容不符合预期，可借助本框架的[流程监控](docs/observability.md)工具进行debug。



