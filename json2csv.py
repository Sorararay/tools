import json
import csv
import os
import sys

def flatten_json(data, prefix=''):
    """
    ネストされたJSONデータをフラットな辞書に変換する。
    キーはドットと角括弧で連結される。
    """
    flat_dict = {}
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            # 再帰的に flatten_json を呼び出し、結果をマージ
            flat_dict.update(flatten_json(value, new_prefix))
    elif isinstance(data, list):
        # 配列が空の場合はキーを生成しない
        if not data:
            # もし空のリスト自体を特定のキーで表現したい場合はここを調整
            pass
        for index, value in enumerate(data):
            new_prefix = f"{prefix}[{index}]"
            # 再帰的に flatten_json を呼び出し、結果をマージ
            flat_dict.update(flatten_json(value, new_prefix))
    else:
        # 基本データ型（文字列、数値、真偽値、Noneなど）の場合
        # prefixが空でない（つまり何らかのキーの下にある値である）場合にのみ追加
        if prefix:
            # ここを value から data に修正
            flat_dict[prefix] = data
    return flat_dict

def main(json_filepath, output_dir):
    """
    指定されたJSONファイルを読み込み、'resources'配列を処理し、
    'types'の値ごとにCSVファイルを生成する。
    'types'が文字列の場合も対応。
    """
    # 出力ディレクトリが存在しない場合は作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # JSONファイルを読み込む
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input JSON file not found at '{json_filepath}'", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{json_filepath}'. Please check the file format.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading the JSON file: {e}", file=sys.stderr)
        sys.exit(1)

    # 'resources'キーが存在し、かつリストであることを確認
    resources = data.get('resources')
    if not isinstance(resources, list):
        print("Error: JSON data does not contain a 'resources' key, or it is not a list.", file=sys.stderr)
        sys.exit(1)

    # タイプごとのデータを格納する辞書
    # キー: typeの値 (文字列)
    # 値: そのタイプのflattenされたオブジェクトのリスト
    data_by_type = {}

    # 各リソースオブジェクトを処理
    for i, resource in enumerate(resources):
        if not isinstance(resource, dict):
            print(f"Warning: Skipping item at index {i} in 'resources' as it is not an object: {resource}", file=sys.stderr)
            continue

        types_value = resource.get('types')
        resource_id = resource.get('id', 'N/A') # ログ出力用にIDを取得

        # 'types'キーが存在し、文字列またはリストであることを確認
        if types_value is None:
             print(f"Warning: Resource (ID: {resource_id}) at index {i} has no 'types' key. Skipping.", file=sys.stderr)
             continue

        # types_value をリストに変換（文字列の場合は単一要素リストに）
        if isinstance(types_value, str):
            types_list = [types_value]
        elif isinstance(types_value, list):
            # リストだが空の場合はスキップ
            if not types_value:
                print(f"Warning: Resource (ID: {resource_id}) at index {i} has an empty 'types' list. Skipping.", file=sys.stderr)
                continue
            types_list = types_value
        else:
            print(f"Warning: Resource (ID: {resource_id}) at index {i} has 'types' value that is neither a string nor a list ({type(types_value)}). Skipping.", file=sys.stderr)
            continue


        # オブジェクトをフラット化
        try:
             flattened_resource = flatten_json(resource)
        except Exception as e:
             print(f"Error flattening resource (ID: {resource_id}) at index {i}: {e}", file=sys.stderr)
             # エラーが発生したリソースはスキップ
             continue

        # 各タイプごとにデータを分類
        for res_type in types_list:
            if not isinstance(res_type, str):
                print(f"Warning: Skipping non-string type '{res_type}' found in resource (ID: {resource_id}) at index {i}.", file=sys.stderr)
                continue

            # タイプ名をキーとして辞書にデータを追加
            if res_type not in data_by_type:
                data_by_type[res_type] = []
            data_by_type[res_type].append(flattened_resource)

    # タイプごとにCSVファイルを作成
    if not data_by_type:
        print("No resources with valid 'types' found to generate CSV files.", file=sys.stderr)
        sys.exit(0) # 処理は完了したが、出力ファイルはなし

    for res_type, flattened_objects in data_by_type.items():
        if not flattened_objects:
            # ここには来ないはずだが念のため
            continue

        # そのタイプのすべてのオブジェクトからユニークなキー（カラム名）を収集
        all_keys_for_type = set()
        for obj in flattened_objects:
            all_keys_for_type.update(obj.keys())

        # カラムの順序を一定にするためにソート
        sorted_keys = sorted(list(all_keys_for_type))

        # CSVファイル名とパスを生成
        # ファイル名に使えない文字が含まれる可能性を考慮する必要がある場合は sanitizing が必要です。
        # 例えば、'/','\'などはファイル名に使えません。ここでは単純な置換例を示します。
        sanitized_type = res_type.replace('/', '_').replace('\\', '_') # 例: / や \ を _ に置換
        output_filename = f"{sanitized_type}.csv"
        output_filepath = os.path.join(output_dir, output_filename)

        # CSVファイルを書き込み
        try:
            with open(output_filepath, 'w', newline='', encoding='utf-8') as csvfile:
                # DictWriterを使用すると、辞書データの書き込みが容易になります
                writer = csv.DictWriter(csvfile, fieldnames=sorted_keys)

                # ヘッダー行を書き込み
                writer.writeheader()

                # データ行を書き込み
                # DictWriterは fieldnames に存在しないキーを無視します。
                # fieldnames に存在してもオブジェクトにキーがない場合は空のセルになります。
                writer.writerows(flattened_objects)

            print(f"Successfully created CSV file: '{output_filepath}'")

        except IOError as e:
            print(f"Error writing CSV file '{output_filepath}': {e}", file=sys.stderr)
        except Exception as e:
            print(f"An unexpected error occurred while writing CSV file '{output_filepath}': {e}", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python json_to_csv_by_type.py <input_json_file> <output_directory>", file=sys.stderr)
        sys.exit(1)

    input_json_file = sys.argv[1]
    output_directory = sys.argv[2]

    main(input_json_file, output_directory)
