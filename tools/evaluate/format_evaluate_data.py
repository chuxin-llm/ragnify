
import json
import argparse
import requests

parser = argparse.ArgumentParser(prog='rag-evaluation',
                                     description='')
parser.add_argument("--ip", type=str)
parser.add_argument("--port", type=str)
parser.add_argument("--knowledge_base_name", type=str)
parser.add_argument("--org_file_path", type=str)
parser.add_argument("--dump_file_path", type=str)

args = parser.parse_args()


########################################################
# Step 1. 加载原始数据（json格式，只包含filename、question、gt_context、gt_answer信息）
########################################################
f = open(args.org_file_path)
data = json.load(f)
print(data[0])

########################################################
# Step 2. 调用知识对话接口，得到context、answer
########################################################
url = "http://" + args.ip + ":" + args.port + "/chat/knowledge_base_chat"  # 接口URL
headers = {
  'Content-Type': 'application/json'
}
payload = {"query": "", "knowledge_base_name": args.knowledge_base_name, "history": [], "stream": False, "return_docs": True}  # 请求参数
for d in data:
    payload.update({"query": d["question"]})
    response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
    result = json.loads(response.text.split("data: ")[-1])
    # context = "\n".join([doc["context"] for doc in result["docs"]])
    context = [doc["context"] for doc in result["docs"]]
    answer = result["result"]
    d.update({"context": context, "answer": answer})

########################################################
# Step 3. 将数据写回文件
########################################################
with open(args.dump_file_path, 'w') as f:
    json.dump(data, f, ensure_ascii=False)
