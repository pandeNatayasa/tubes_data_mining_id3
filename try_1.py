# SUmber : https://github.com/tofti/python-id3-trees

import ast
import csv
import sys
import math
import os

# Library untuk test
import json


def load_csv_to_header_data(filename):
    # print("filename : "+filename) # mengecek direktori
    fpath = os.path.join(os.getcwd(), filename) 
    # print("path : "+fpath) # mengecek direktori ditambahkan path sesuai folder pada laptop yang digunakan
    fs = csv.reader(open(fpath))

    all_row = [] # untuk menyimpan hasil pembacaan csv
    for r in fs:
        all_row.append(r)

    headers = all_row[0]
    idx_to_name, name_to_idx = get_header_name_to_idx_maps(headers) # This is to get index and name of index

    data = {
        'header': headers,
        'rows': all_row[1:],
        'name_to_idx': name_to_idx,
        'idx_to_name': idx_to_name
    }
    # print("data : "+idx_to_name[0])
    return data


def get_header_name_to_idx_maps(headers):
    name_to_idx = {}
    idx_to_name = {}
    for i in range(0, len(headers)):
        name_to_idx[headers[i]] = i
        # print("name_to_idx ["+str(headers[i])+"]: "+str(i))
        idx_to_name[i] = headers[i]
        # print("idx_to_name ["+str(i)+"]: "+str(headers[i]))
    return idx_to_name, name_to_idx


def project_columns(data, columns_to_project):
    data_h = list(data['header'])
    data_r = list(data['rows'])

    all_cols = list(range(0, len(data_h)))

    columns_to_project_ix = [data['name_to_idx'][name] for name in columns_to_project]
    columns_to_remove = [cidx for cidx in all_cols if cidx not in columns_to_project_ix]

    for delc in sorted(columns_to_remove, reverse=True):
        # print("delc : " + delc)
        del data_h[delc]
        for r in data_r:
            del r[delc]

    idx_to_name, name_to_idx = get_header_name_to_idx_maps(data_h)

    return {'header': data_h, 'rows': data_r,
            'name_to_idx': name_to_idx,
            'idx_to_name': idx_to_name}


def get_uniq_values(data):
    idx_to_name = data['idx_to_name']
    idxs = idx_to_name.keys()

    val_map = {}
    for idx in iter(idxs):
        val_map[idx_to_name[idx]] = set()

    for data_row in data['rows']:
        for idx in idx_to_name.keys():
            att_name = idx_to_name[idx]
            val = data_row[idx]
            if val not in val_map.keys():
                val_map[att_name].add(val)
    return val_map


def get_class_labels(data, target_attribute):
    rows = data['rows']
    col_idx = data['name_to_idx'][target_attribute]
    labels = {}
    for r in rows:
        val = r[col_idx]
        if val in labels:
            labels[val] = labels[val] + 1
        else:
            labels[val] = 1
    return labels


def entropy(n, labels): # Function to calculate entropy
    ent = 0
    for label in labels.keys():
        # print( "labels["+label+"] : "+str(labels[label]))
        p_x = labels[label] / n
        ent += - p_x * math.log(p_x, 2) # Rumus entropy

    # print("entropy : "+str(ent))
    return ent


def partition_data(data, group_att):
    partitions = {}
    data_rows = data['rows']
    partition_att_idx = data['name_to_idx'][group_att]
    for row in data_rows:
        row_val = row[partition_att_idx]
        if row_val not in partitions.keys():
            partitions[row_val] = {
                'name_to_idx': data['name_to_idx'],
                'idx_to_name': data['idx_to_name'],
                'rows': list()
            }
        partitions[row_val]['rows'].append(row)
    return partitions


def avg_entropy_w_partitions(data, splitting_att, target_attribute):
    # find uniq values of splitting att
    data_rows = data['rows']
    n = len(data_rows)
    partitions = partition_data(data, splitting_att)

    avg_ent = 0

    for partition_key in partitions.keys():
        partitioned_data = partitions[partition_key]
        partition_n = len(partitioned_data['rows'])
        partition_labels = get_class_labels(partitioned_data, target_attribute)
        partition_entropy = entropy(partition_n, partition_labels)
        avg_ent += partition_n / n * partition_entropy

    return avg_ent, partitions


def most_common_label(labels):
    mcl = max(labels, key=lambda k: labels[k])
    return mcl


def id3(data, uniqs, remaining_atts, target_attribute):
    labels = get_class_labels(data, target_attribute) # to get total of playtenis when yes and no

    # print(" labels : ")
    # print(labels)
    # print(" labels keys : ")
    # print(labels.keys())

    node = {}

    # belum di ketahui tujuannya
    if len(labels.keys()) == 1:
        node['label'] = next(iter(labels.keys()))
        return node

    if len(remaining_atts) == 0:
        node['label'] = most_common_label(labels)
        return node
    # akhir belum di ketahui tujuannya

    n = len(data['rows']) # To get total data
    # print(n)
    ent = entropy(n, labels) # to get entropy total

    # Bagian yang belum dipahami
    max_info_gain = None
    max_info_gain_att = None
    max_info_gain_partitions = None

    for remaining_att in remaining_atts:
        
        # untuk memperoleh entropy setiap bagian data, dan partitions = bagian datanya
        avg_ent, partitions = avg_entropy_w_partitions(data, remaining_att, target_attribute) 

        info_gain = ent - avg_ent # untuk menghitung gain

        # Bagian ini untuk memperoleh max_info_gain = gain terbesar setiap iterasi, 
        # max_info_gain_att = atribut yang gainnya terbesar, max_info_gain_partitions = partisi atau bagian data dengan gain terbesar
        if max_info_gain is None or info_gain > max_info_gain:
            max_info_gain = info_gain
            max_info_gain_att = remaining_att
            max_info_gain_partitions = partitions

    # Jika sudah semua data masuk ke dalam pohon yang dihasilkan maka :
    if max_info_gain is None:
        node['label'] = most_common_label(labels)
        return node

    node['attribute'] = max_info_gain_att # Simpan atribut dengan gain terbesar ke array node dengan index attribute
    node['nodes'] = {}

    # Start
    remaining_atts_for_subtrees = set(remaining_atts)
    remaining_atts_for_subtrees.discard(max_info_gain_att)

    uniq_att_values = uniqs[max_info_gain_att] # untuk mendapatkan atribut untuk bagian dengan gain terbesar
    # print("max_info_gain_att : "+ max_info_gain_att)
    # print("uniq_att_values : ")
    # print(uniq_att_values)
    # print("max_info_gain_partitions : ")
    # print(max_info_gain_partitions)


    with open('data.json', 'w') as outfile:
        json.dump(max_info_gain_partitions, outfile , indent = 4)

    for att_value in uniq_att_values:
        if att_value not in max_info_gain_partitions.keys():
            node['nodes'][att_value] = {'label': most_common_label(labels)}
            continue
        partition = max_info_gain_partitions[att_value]
        node['nodes'][att_value] = id3(partition, uniqs, remaining_atts_for_subtrees, target_attribute) # bagian rekursif

    return node
    # Bagian akhir yang belum dipahami


def load_config(config_file):
    with open(config_file, 'r') as myfile:
        data = myfile.read().replace('\n', '')
    return ast.literal_eval(data)


def pretty_print_tree(root):
    stack = []
    rules = set()

    def traverse(node, stack, rules):
        if 'label' in node:
            stack.append(' THEN ' + node['label'])
            rules.add(''.join(stack))
            stack.pop()
        elif 'attribute' in node:
            ifnd = 'IF ' if not stack else ' AND '
            stack.append(ifnd + node['attribute'] + ' EQUALS ')
            for subnode_key in node['nodes']:
                stack.append(subnode_key)
                traverse(node['nodes'][subnode_key], stack, rules)
                stack.pop()
            stack.pop()

    traverse(root, stack, rules)
    print(os.linesep.join(rules))


def main():
    # argv = sys.argv
    # print("Command line args are {}: ".format(argv))

    config = load_config('./tennis.cfg')
    # config = load_config('./resources/credithistory.cfg')

    data = load_csv_to_header_data(config['data_file'])
    # print("data after load csv to header : ")
    # print(data)
    # data = project_columns(data, config['data_project_columns'])
    # print("data project columns : ")
    # print(data)

    target_attribute = config['target_attribute']
    remaining_attributes = set(data['header'])
    # print("remaining_attributes : ")
    # print(remaining_attributes)

    remaining_attributes.remove(target_attribute)
    # print("remaining_attributes : ")
    # print(remaining_attributes)    

    uniqs = get_uniq_values(data) # To get atribut unique every row in data
    # print("uniqs : ")
    # print(uniqs)

    root = id3(data, uniqs, remaining_attributes, target_attribute)

    # print(root);

    pretty_print_tree(root)


if __name__ == "__main__": main()
