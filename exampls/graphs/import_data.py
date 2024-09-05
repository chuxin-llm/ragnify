
import json
import hashlib
import os
import sys
import argparse


parser = argparse.ArgumentParser(prog='Import data to NebulaGraph', description='')
parser.add_argument("--ip", type=str, default="")
parser.add_argument("--port", type=int, default=7001)
parser.add_argument("--file_path", type=str, default="")
parser.add_argument("--space", type=str, default="")

args = parser.parse_args()


def md5_encryption(data):
    md5 = hashlib.md5()
    md5.update(data.encode('utf-8'))
    return md5.hexdigest()


# 共７类节点
drugs = []                  # 药品
foods = []                  # 食物
checks = []                 # 检查
departments = []            # 科室
producers = []              # 药品厂商
diseases = []               # 疾病
symptoms = []               # 症状

# 疾病节点的属性
disease_infos = []          # 疾病信息

# 关系
rels_department_belongs_to = []         # 科室－科室关系
rels_disease_no_eat = []                # 疾病－忌吃食物关系
rels_disease_do_eat = []                # 疾病－宜吃食物关系
rels_disease_recommend_eat = []         # 疾病－推荐吃食物关系
rels_disease_common_drug = []           # 疾病－通用药品关系
rels_disease_recommend_drug = []        # 疾病－推荐药品关系
rels_disease_need_check = []            # 疾病－检查关系
rels_drugs_of = []                      # 厂商－药物关系

rels_has_symptom = []                   # 疾病症状关系：disease - symptom
rels_disease_acompany_with = []         # 疾病并发关系：disease - disease
rels_disease_department = []            # 疾病与科室之间的关系：disease - department

count = 0
file_path = ""
for data in open(file_path, encoding='utf-8'):
    disease_dict = {}
    count += 1
    print(count)
    data_json = json.loads(data)
    disease_name = data_json["name"]
    disease_dict['name'] = disease_name
    diseases.append(disease_name)

    disease_dict['desc'] = ''
    disease_dict['prevent'] = ''
    disease_dict['cause'] = ''
    disease_dict['easy_get'] = ''
    disease_dict['cure_department'] = ''
    disease_dict['cure_way'] = ''
    disease_dict['cure_lasttime'] = ''
    disease_dict['symptom'] = ''
    disease_dict['cured_prob'] = ''

    if 'symptom' in data_json:
        symptoms += data_json['symptom']
        for symptom in data_json['symptom']:
            rels_has_symptom.append([disease_name, symptom])

    if 'acompany' in data_json:
        for acompany in data_json['acompany']:
            rels_disease_acompany_with.append([disease_name, acompany])

    if 'desc' in data_json:
        disease_dict['desc'] = data_json['desc'].replace("\n", "\\n").replace("\"", '\\"')

    if 'prevent' in data_json:
        disease_dict['prevent'] = data_json['prevent'].replace("\n", "\\n").replace("\"", '\\"')

    if 'cause' in data_json:
        disease_dict['cause'] = data_json['cause'].replace("\n", "\\n").replace("\"", '\\"')

    if 'cure_department' in data_json:
        cure_department = data_json['cure_department']
        if len(cure_department) == 1:
            rels_disease_department.append([disease_name, cure_department[0]])
        if len(cure_department) == 2:
            big = cure_department[0]
            small = cure_department[1]
            rels_department_belongs_to.append([small, big])
            rels_disease_department.append([disease_name, small])

        disease_dict['cure_department'] = cure_department
        departments += cure_department

    if 'cure_way' in data_json:
        disease_dict['cure_way'] = "、".join(data_json['cure_way'])

    if 'cure_lasttime' in data_json:
        disease_dict['cure_lasttime'] = data_json['cure_lasttime']

    if 'cured_prob' in data_json:
        disease_dict['cured_prob'] = data_json['cured_prob']

    if 'common_drug' in data_json:
        common_drug = data_json['common_drug']
        for drug in common_drug:
            rels_disease_common_drug.append([disease_name, drug])
        drugs += common_drug

    if 'recommand_drug' in data_json:
        recommand_drug = data_json['recommand_drug']
        drugs += recommand_drug
        for drug in recommand_drug:
            rels_disease_recommend_drug.append([disease_name, drug])

    if 'not_eat' in data_json:
        not_eat = data_json['not_eat']
        for _not in not_eat:
            rels_disease_no_eat.append([disease_name, _not])
        foods += not_eat

        do_eat = data_json['do_eat']
        for _do in do_eat:
            rels_disease_do_eat.append([disease_name, _do])
        foods += do_eat

    if 'recommand_eat' in data_json:
        recommand_eat = data_json['recommand_eat']
        for _recommand in recommand_eat:
            rels_disease_recommend_eat.append([disease_name, _recommand])
        foods += recommand_eat

    if 'check' in data_json:
        check = data_json['check']
        for _check in check:
            rels_disease_need_check.append([disease_name, _check])
        checks += check

    if 'drug_detail' in data_json:
        drug_detail = data_json['drug_detail']
        for i in drug_detail:
            producer = i.split('(')[0]
            drug = i.split('(')[-1].replace(')', '')
            rels_drugs_of.append([producer, drug])
            producers.append(producer)
            drugs.append(drug)

    disease_infos.append(disease_dict)


# 去重
drugs = list(set(drugs))
foods = list(set(foods))
checks = list(set(checks))
departments = list(set(departments))
producers = list(set(producers))
symptoms = list(set(symptoms))


import os
from nebula3.Config import SessionPoolConfig
from nebula3.gclient.net.SessionPool import SessionPool
config = SessionPoolConfig()

# init session pool
IP = args.ip
PORT = args.port
SPACE = args.space
session_pool = SessionPool('root', 'nebula', SPACE, [(IP, PORT)])
assert session_pool.init(config)

BATCH_SIZE = 10


def import_nodes(node_type, node_list, info=None):
    node_dict = {}
    if node_type == "disease":
        assert len(node_list) == len(info)
        for i, node_name in enumerate(node_list):
            if node_name in node_dict: continue

            vid_text = node_type + "_" + node_name
            vid = md5_encryption(vid_text)
            node_info = info[i]
            desc = node_info.get("desc", "")
            cause = node_info.get("cause", "")
            prevent = node_info.get("prevent", "")
            cure_lasttime = node_info.get("cure_lasttime", "")
            cure_way = node_info.get("cure_way", "")
            cured_prob = node_info.get("cured_prob", "")
            easy_get = node_info.get("easy_get", "")

            line = f'"{vid}":("{node_name}", "{desc}", "{cause}", "{prevent}", "{cure_lasttime}", "{cure_way}", "{cured_prob}", "{easy_get}")'
            node_dict[node_name] = line

    else:
        for i, node_name in enumerate(node_list):
            vid_text = node_type + "_" + node_name
            vid = md5_encryption(vid_text)

            line = f'"{vid}":("{node_name}")'
            node_dict[node_name] = line

    error_num = 0
    node_names = list(node_dict.keys())
    epoch_num = len(node_names) // BATCH_SIZE + 1
    for i in range(epoch_num):
        epoch_node_names = node_names[i * BATCH_SIZE: (i+1) * BATCH_SIZE]
        nodes = [node_dict[n] for n in epoch_node_names]
        if len(nodes) == 0: continue
        value = ",".join(nodes)
        if node_type == "disease":
            cmd_line = 'INSERT VERTEX disease(name, description, cause, prevent, cure_lasttime, cure_way, cured_prob, easy_get) VALUES ' + value
        else:
            cmd_line = 'INSERT VERTEX ' + node_type + '(name) VALUES ' + value
        try:
            resp = session_pool.execute(cmd_line)
            assert resp.is_succeeded(), resp.error_msg()
        except Exception as e:
            print(i, node_names[i], e)
            print(cmd_line)
            os._exit(0)
            error_num += len(nodes)

print("\n\n\n")
import_nodes("disease", diseases, disease_infos)
import_nodes("drug", drugs)
import_nodes("food", foods)
import_nodes("check", checks)
import_nodes("department", departments)
import_nodes("producer", producers)
import_nodes("symptom", symptoms)


# 插入关系边
node_vids = {
    "disease": [md5_encryption("disease" + "_" + disease) for disease in diseases],
    "drug": [md5_encryption("drug" + "_" + drug) for drug in drugs],
    "food": [md5_encryption("food" + "_" + food) for food in foods],
    "check": [md5_encryption("check" + "_" + check) for check in checks],
    "department": [md5_encryption("department" + "_" + department) for department in departments],
    "producer": [md5_encryption("producer" + "_" + producer) for producer in producers],
    "symptom": [md5_encryption("symptom" + "_" + symptom) for symptom in symptoms],
}


def distinct_edge(rels):
    set_edges = []
    for edge in rels: set_edges.append('###'.join(edge))

    edges = []
    for edge in set(set_edges):
        edge = edge.split("###")
        p, q = edge[0], edge[1]
        edges.append([p, q])
    return edges


rels_department_belongs_to = distinct_edge(rels_department_belongs_to)
rels_disease_no_eat = distinct_edge(rels_disease_no_eat)
rels_disease_do_eat = distinct_edge(rels_disease_do_eat)
rels_disease_recommend_eat = distinct_edge(rels_disease_recommend_eat)
rels_disease_common_drug = distinct_edge(rels_disease_common_drug)
rels_disease_recommend_drug = distinct_edge(rels_disease_recommend_drug)
rels_drugs_of = distinct_edge(rels_drugs_of)
rels_has_symptom = distinct_edge(rels_has_symptom)
rels_disease_acompany_with = distinct_edge(rels_disease_acompany_with)
rels_disease_department = distinct_edge(rels_disease_department)


def import_edges(rels, source_node_type, target_node_type, rel_name):
    error_num = 0
    source_node_vids, target_node_vids = node_vids[source_node_type], node_vids[target_node_type]
    for i, rel in enumerate(rels):
        source_node_vid = md5_encryption(source_node_type + "_" + rel[0])
        target_node_vid = md5_encryption(target_node_type + "_" + rel[1])
        if source_node_vid not in source_node_vids or target_node_vid not in target_node_vids:
            error_num += 1
        else:
            try:
                resp = session_pool.execute(
                    'INSERT EDGE {}() VALUES "{}"->"{}":();'.format(rel_name, source_node_vid, target_node_vid)
                )
                assert resp.is_succeeded(), resp.error_msg()
            except Exception as e:
                print(source_node_vid, target_node_vid, e)
                error_num += 1

print("\n\n\n")
import_edges(rels_department_belongs_to, "department", "department", "department_belongs_to")
import_edges(rels_disease_no_eat, "disease", "food", "disease_no_eat")
import_edges(rels_disease_do_eat, "disease", "food", "disease_do_eat")
import_edges(rels_disease_recommend_eat, "disease", "food", "disease_recommend_eat")
import_edges(rels_disease_common_drug, "disease", "drug", "disease_common_drug")
import_edges(rels_disease_recommend_drug, "disease", "drug", "disease_recommend_drug")
import_edges(rels_drugs_of, "producer", "drug", "drugs_of")
import_edges(rels_has_symptom, "disease", "symptom", "disease_has_symptom")
import_edges(rels_disease_acompany_with, "disease", "disease", "disease_accompany_with")
import_edges(rels_disease_department, "disease", "department", "disease_department")