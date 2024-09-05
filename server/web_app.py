
import os, sys
sys.path.append(os.getcwd())
import streamlit as st
import requests

log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
if not os.path.exists(log_dir):
    os.mkdir(log_dir)

from server.utils import ApiRequest
from rag.common.configuration import settings
VECTOR_STORE_TYPE = settings.vector_store.type
EMB_MODEL = settings.embeddings.model_name_or_path


def web():

    from rag.common.configuration import settings

    base_url = "http://127.0.0.1:" + str(settings.server.api_server_port)

    try:
        is_service_up = requests.get(base_url+"/docs")
        if is_service_up.status_code == 200:
            api = ApiRequest(base_url=base_url)
        else:
            st.error(f"Api Server没正确启动！")
    except requests.exceptions.RequestException:
        st.error(f"请先启动Api Server！")

    ########################################################
    # Knowledge Base
    ########################################################
    from rag.connector.database.repository.knowledge_file_repository import delete_files_from_db, list_files_from_db
    from rag.connector.database.repository.knowledge_base_repository import list_kbs_from_db

    st.set_page_config(layout="wide")

    with (st.sidebar):
        knowledge_base_list = list_kbs_from_db()[::-1]

        if "selected_kb_name" in st.session_state and st.session_state["selected_kb_name"] in knowledge_base_list:
            selected_kb_index = knowledge_base_list.index(st.session_state["selected_kb_name"])
        else:
            selected_kb_index = 0

        selected_kb = st.selectbox(
            "请选择或新建知识库：",
            knowledge_base_list + ["新建知识库"],
            index=selected_kb_index
        )

        if selected_kb == "新建知识库":
            with st.form("create_kb", clear_on_submit=True, border=False):
                kb_name = st.text_input(
                    "请输入知识库名称：",
                    placeholder="新知识库名称，不支持中文命名",
                    key="kb_name",
                )
                submit_create_kb = st.form_submit_button("新      建", use_container_width=True)

            if submit_create_kb:
                if not kb_name or not kb_name.strip():
                    st.error(f"知识库名称不能为空！")
                elif kb_name in knowledge_base_list:
                    st.error(f"名为 {kb_name} 的知识库已经存在！")
                else:
                    resp = api.create_knowledge_base(
                        knowledge_base_name=kb_name,
                        vector_store_type=VECTOR_STORE_TYPE
                    )
                    if resp.get("code") == 200:
                        st.rerun()
                    else:
                        st.error(f"知识库 {kb_name} 创建失败")

        elif selected_kb:
            with st.form("上传文件到知识库", clear_on_submit=True):
                st.subheader("上传文件到知识库")
                uploaded_files = st.file_uploader("", accept_multiple_files=True)
                submitted = st.form_submit_button("上传")

            placeholder = st.empty()
            exist_files = [os.path.basename(f) for f in list_files_from_db(selected_kb)]
            with placeholder.container():
                if len(exist_files) > 0:
                    st.subheader("知识库中已有文件:")
                    for file_name in exist_files:
                        st.write(file_name)
                else:
                    st.subheader("当前知识库为空")

            if uploaded_files and submitted:
                st.info(f"正在上传 {len(uploaded_files)} 个文件到知识库 {selected_kb}")
                resp = api.upload_kb_docs(uploaded_files, selected_kb)

                code = resp.get("code")
                if code == 200:
                    failed_files = resp.get("failed_files")
                    if failed_files:
                        for f in failed_files: print(f, failed_files[f])
                        msg = "下列文件上传失败: " + "\n".join([os.path.basename(f_name) for f_name in list(failed_files.keys())])
                        st.error(msg)
                    else:
                        st.success(f"所有文件上传成功!")
                else:
                    st.error(f"文件上传失败！")

                exist_files = [os.path.basename(f) for f in list_files_from_db(selected_kb)]
                with placeholder.container():
                    if len(exist_files) > 0:
                        st.subheader("知识库中已有文件:")
                        for file_name in exist_files:
                            st.write(file_name)
                    else:
                        st.subheader("当前知识库为空")

            with st.sidebar:
                cols = st.columns(2)
                if cols[0].button(
                    "清空知识库",
                    use_container_width=True,
                ):
                    res = api.clear_knowledge_base(selected_kb)
                    if res.get("code") == 200:
                        placeholder.subheader("当前知识库为空")
                    else:
                        st.error(f"清空当前知识库 {selected_kb} 失败！")


    ########################################################
    # LLM Response Generation and Chat
    ########################################################
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["context"])

    if prompt := st.chat_input("请输入您的问题: "):
        if selected_kb not in knowledge_base_list:
            st.error("对话前请选择一个知识库！")
        else:
            st.chat_message("user").markdown(prompt)                                # 显示用户消息
            st.session_state.messages.append({"role": "user", "context": prompt})   # 将用户消息存入历史记录

            with st.chat_message("assistant"):  # 显示机器人回复
                message_placeholder = st.empty()
                full_response = ""
                for res in api.knowledge_base_chat(prompt, knowledge_base_name=selected_kb):
                    full_response = res
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
            # 将回复存入历史记录
            st.session_state.messages.append({"role": "assistant", "context": full_response})


if __name__ == "__main__":
    web()
