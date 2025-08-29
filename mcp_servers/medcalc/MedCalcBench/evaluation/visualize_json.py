import json
import os
import re
import sys

def safe_sentence_break(text):
    # Avoid breaking after known exceptions
    pattern = r'(?<!\bFig)(?<!\bFigs)\. '
    return re.sub(pattern, '.\n', text)

def pretty_print_jsonl_to_file(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-8') as f_in, \
             open(output_path, 'w', encoding='utf-8') as f_out:

            for i, line in enumerate(f_in, 1):
                try:
                    obj = json.loads(line)
                    pretty = json.dumps(obj, indent=4, ensure_ascii=False)

                    # Apply safe sentence breaking
                    pretty = safe_sentence_break(pretty)

                    f_out.write(f"\n--- Entry {i} ---\n")
                    f_out.write(pretty + "\n")
                except json.JSONDecodeError as e:
                    f_out.write(f"\nError decoding line {i}: {e}\n")
                    f_out.write(line.strip() + "\n")

    except Exception as e:
        print(f"Failed to convert {input_path}: {e}")

def convert_all_jsonl_in_folder(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Not a valid folder: {folder_path}")
        return

    for filename in os.listdir(folder_path):
        if filename.endswith('.jsonl'):
            jsonl_path = os.path.join(folder_path, filename)
            txt_path = os.path.join(folder_path, filename.replace('.jsonl', '_pretty.txt'))
            print(f"Converting: {filename} -> {os.path.basename(txt_path)}")
            pretty_print_jsonl_to_file(jsonl_path, txt_path)

if __name__ == '__main__':
    folder = './MedCalcBench/evaluation/outputs'
    convert_all_jsonl_in_folder(folder)
