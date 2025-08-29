__author__ = "qiao"

import json
import contextlib
import os
import io
import re
import traceback
import sys
import pandas as pd
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import openai
from run import extract_answer
from evaluate import check_correctness
import numpy as np
from table_stats import compute_overall_accuracy


openai.api_key = os.getenv("OPENAI_API_KEY") 


def capture_exec_output_and_errors(code):
    """
    Executes the given code and captures its printed output and any error messages.

    Parameters:
    code (str): The Python code to execute.

    Returns:
    str: The captured output and error messages of the executed code.
    """
    globals = {}

    with io.StringIO() as buffer, contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
        try:
            exec(code, globals)
        except Exception as e:
            # Print the error to the buffer
            traceback.print_exc()

        return buffer.getvalue()


def extract_python_code(text):
    pattern = r"```python\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return "\n".join(matches)


def apply_calc(question, patient_note, model_name):
    system = f"You are a helpful assistant. Your task is to read a patient note and compute a medical value based on the following the question: {question}.\n"
    system += "If there are multiple values for a given measurement or attribute, then please use the value recorded based on when the patient note was written. You should not be using values that the patient had post-treatment or values from a patient's history in the past. "
    system += "Additionally, if the problem doesn't directly imply or provide information regarding a particular patient attribute, assume the patient does not have it."
    system += "Do not perform any computations yourself. Do not state a numerical answer. First write code for any equations you are using and then plug in values based on the patient note. Make sure the code prints all of its outputs."
    system += "If there are any errors with compiling your script, you may need to re-write your code to obtain the output. Note that all of the necessary information is provided in the patient note and you should not need to prompt the user for any information."
    system += "When you are finished with all the computations, please output your final answer value in the following format: <answer> YOUR_ANSWER_HERE <\\answer>, where YOUR_ANSWER_HERE is your final answer value without any units (examples: <answer> 17.29 <\\answer> (an example answer where the output can be a decimal), <answer> 5 <\\answer> (an example answer for score-based problems), <answer> 5/4/2021 <\\answer> (an example answer for estimated date problems), <answer> (4 weeks, 3 days) <\\answer> (an example answer for estimated gestational age))."
    system += "Asides for the step where you give your final answer in the <answer> <\\answer> tags, all your other responses must ALWAYS have code with the ```python tag as part of your response. This code should all be written in a single block used for computing the final answer value. The last statement in your code should be a print() statement so that the user can execute your code and provide you with the final answer. "

    prompt = "Patient Note:\n\n"
    prompt += patient_note + "\n\n"
    prompt += "Question:\n\n"
    prompt += question + "\n\n"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    n = 0

    while True:
        response = openai.ChatCompletion.create(
                    model=model_name,
                    messages=messages
        )

        output = response.choices[0].message.content

        n += 1
        print(f"Round {n}\n")
        print("LLM OUTPUT:\n")
        print(output)
        print("\n")

        messages.append({"role": "assistant", "content": output})

        if "<answer>" in output and "<\\answer>" in output:
            match_ = re.search(r'<answer>(.*?)<\\answer>', output)

            if match_:
                answer = match_.group(1).strip()
                messages.append({"role": "user", "content": str(answer)})
                return str(answer), messages
        else:
            message_code = extract_python_code(output)

            if "```python" not in output:
                new_output = f"It seems that you have not written any code as part of your response. This was your last thought:\n\n\n{output}\n\n\n. Based on this, please write a single block of code which the user will execute for you so that you can obtain the final answer. To get the final answer value from the console, please add a print() statement at the end, i.e. print(creatinine_clearance), print(bmi), print(curb-65 score)"
                print("MESSAGE CODE:\n")
                print(message_code)
                print("\n")
                messages.append({"role": "user", "content": new_output})

            elif "print" not in message_code:
                new_output = f"This was your previous response:\n\n\n{output}\n\n\n. There is no print() statement in your code. Please add a print statement to your code so that the user can execute your code for you to print out the value of the final answer value, i.e. print(creatinine_clearance), print(bmi), print(curb-65 score) "
                messages.append({"role": "user", "content": new_output})

            elif "input(" in message_code:
                return "N/A", messages
            else:

                console_output = capture_exec_output_and_errors(message_code)
                
                new_output = f"""I have executed your code, and the output is:

                {console_output}

                If there was an error, or the computed answer is obviously incorrect, please revise your code. Otherwise please output your final answer in the following format:

                <answer> YOUR_ANSWER_HERE <\\answer> where YOUR_ANSWER_HERE is your final answer.

                Decimal Example:
                <answer> 17.29 <\\answer>

                Score-Based Example:
                <answer> 5 <\\answer>

                Estimated Date Example:
                <answer> 5/21/2021 <\\answer>

                Estimated Age Example:
                <answer> (4 weeks, 3 days) <\\answer>

                All of the information needed is in the patient note and you should not need to prompt the user for any more information.
                """

                print("CONSOLE OUTPUT:\n")
                print(console_output)
                print("\n")

                messages.append({"role": "user", "content": new_output})

        if n >= 20:
            return None, messages


def process_row(row, model_name):
    return apply_calc(row["Question"], row["Patient Note"], model_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse arguments')
    parser.add_argument('--gpt', type=float, help='Specify GPT version')

    args = parser.parse_args()

    gpt_model = str(int(args.gpt))

    if gpt_model == "4":
        gpt_model = "gpt-4"
        model_name = "gpt_4"
    elif gpt_model == "35":
        gpt_model = "gpt-3.5-turbo-16k"
        model_name = "gpt_35_16k"

    evaluations = {}

    df = pd.read_csv("../dataset/test_data.csv")

    if not os.path.exists("outputs"):
        os.makedirs("outputs")

    output_path = f"code_exec_{model_name}.jsonl" 

    if os.path.exists("outputs/" + output_path):
        existing = pd.read_json(output_path, lines=True)
        existing["Calculator ID"] = existing["Calculator ID"].astype(str)
        existing["Note ID"] = existing["Note ID"].astype(str)

    else:
        existing = None

    count = 0    

    to_execute = {}
    future_to_row = {}

    row_list = []

    for index, row in df.iterrows():

        calc_id = str(row["Calculator ID"])
        note_id = str(row["Note ID"])

        if existing is not None:
            if existing[(existing["Calculator ID"] == calc_id) & (existing["Note ID"] == str(row["Note ID"]))].shape[0] > 0:
                continue
        
        row_list.append(row)

    for row in row_list:

        answer, messages = process_row(row, gpt_model)
        calc_id = str(row["Calculator ID"])
        note_id = str(row["Note ID"])

        if not answer: 
            extracted_answer = "None"
            result = "Incorrect"
        else:
       
            try:
                extracted_answer = extract_answer(f"{{'answer': {answer}}}")
            except:
                extracted_answer = answer

            try:
                status = check_correctness(extracted_answer, row["Ground Truth Answer"], calc_id, row["Upper Limit"], row["Lower Limit"])

                if status:
                    result = "Correct"
                else:
                    result = "Incorrect"

            except:
                result = "Incorrect"
                
            
        outputs = {
            "Row Number": int(row["Row Number"]),
            "Calculator Name": row["Calculator Name"],
            "Calculator ID": calc_id,
            "Category": row["Category"],
            "Note ID": note_id,
            "Patient Note": row["Patient Note"],
            "Question": row["Question"], 
            "LLM Answer": extracted_answer,
            "LLM Chat History": messages,
            "Ground Truth Answer": row["Ground Truth Answer"],
            "Ground Truth Explanation": row["Ground Truth Explanation"],
            "Result": result
        }

        with open(f"outputs/{output_path}", "a") as f:
            f.write(json.dumps(outputs) + "\n")

    compute_overall_accuracy(output_path, model_name, "code_augmented")

