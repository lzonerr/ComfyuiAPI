import json
import os


def load_json_files(folder_path):
    # 创建一个空字典来保存所有的数据
    all_data = {}

    # 遍历指定文件夹
    for filename in os.listdir(folder_path):
        # 检查文件是否为.json文件
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)

            # 打开并读取文件
            with open(file_path, 'r', encoding='utf-8') as file:
                try:
                    # 使用json.loads将文件内容转换为字典
                    data = json.load(file)

                    # 将文件名（不包括扩展名）作为键，字典作为值存入all_data
                    all_data[os.path.splitext(filename)[0]] = data
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from {filename}: {e}")

    return all_data


# 使用此文件的同级目录下
folder_path = workflows_folder = os.path.dirname(__file__)
workflows_json = load_json_files(folder_path)

# 输出结果检查
__all__ = ['workflows_json']