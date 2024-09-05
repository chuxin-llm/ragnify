FROM python:3.9

LABEL maintainer=""

# 指定运行时的系统运行变量
ENV APP_NAME llm-rag
ARG APP_VERSION

RUN apt-get update && apt-get install -y libgl1-mesa-glx

# 将应用启动脚本拷贝到镜像中
COPY APP-META/bin/start.sh /home/admin/
RUN chmod +x /home/admin/start.sh

# 将应用配置复制到镜像中
COPY conf/ /home/admin/$APP_NAME/target/$APP_NAME/conf
# 挂载数据卷，指定目录挂载到宿主机上面，为了能够持久化数据以及共享容器间的数据
VOLUME /home/admin/$APP_NAME/target/$APP_NAME/logs \
       /home/admin/$APP_NAME/target/$APP_NAME/conf

# 将构建出的珠宝复制到指定镜像目录中
COPY dist/${APP_NAME}-${APP_VERSION}.tar.gz /home/admin/$APP_NAME/target/

# 启动容器时进入工作目录
WORKDIR /home/admin/$APP_NAME/target/$APP_NAME/

# 容器启动时自动执行的脚本，一般将应用启动脚本放在这里，实现应用自启动
ENTRYPOINT ["/home/admin/start.sh"]

# 将依赖包文件复制到临时目录，安装依赖
ADD requirements.txt /tmp/requirements.txt
RUN pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r /tmp/requirements.txt
RUN cd /home/admin/$APP_NAME/target/ && \
    pip3 install ${APP_NAME}-${APP_VERSION}.tar.gz


