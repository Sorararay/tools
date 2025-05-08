# JSON to CSV Converter by Type

このスクリプトは、指定されたJSONファイルを読み込み、`resources`配列内のデータを`types`キーの値ごとに分類し、それぞれのタイプに対応するCSVファイルを生成します。

## 特徴

- ネストされたJSONデータをフラット化してCSV形式に変換。
- `types`キーの値（文字列またはリスト）ごとにデータを分類。
- 自動的に出力ディレクトリを作成。
- ファイル名に使用できない文字（`/`や`\`など）を安全に置換。

## 必要条件

- Python 3.x
- 標準ライブラリ（追加の外部ライブラリは不要）

## 使用方法

1. スクリプトを実行するには、以下のコマンドを使用します：

   ```bash
   python json2csv.py <input_json_file> <output_directory>