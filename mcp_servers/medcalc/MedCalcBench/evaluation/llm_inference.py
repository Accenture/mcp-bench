__author__ = "guangzhi"
'''
Adapted from https://github.com/Teddy-XiongGZ/MedRAG/blob/main/src/medrag.py
'''
import os
import re
import json
import tqdm
import torch
import time
import asyncio
import argparse
import transformers
from transformers import AutoTokenizer
import openai
from transformers import StoppingCriteria, StoppingCriteriaList
import tiktoken
import openai
import sys
from huggingface_hub import login
from mcp_agent.core.fastagent import FastAgent
import medcalc.calculator as mc
import inspect
from typing import get_type_hints

login(token=os.getenv("HUGGINGFACE_TOKEN"))

openai.api_key = os.getenv("OPENAI_API_KEY") 


class LLMInference:

    def __init__(self, llm_name="OpenAI/gpt-3.5-turbo", cache_dir="../../huggingface/hub"):
        self.llm_name = llm_name
        self.cache_dir = cache_dir
        if self.llm_name.split('/')[0].lower() == "openai":
            self.model = self.llm_name.split('/')[-1]
            if "gpt-3.5" in self.model or "gpt-35" in self.model:
                self.max_length = 4096
            elif "gpt-4" in self.model:
                self.max_length = 8192
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        else:
            self.type = torch.bfloat16
            self.tokenizer = AutoTokenizer.from_pretrained(self.llm_name, cache_dir=self.cache_dir, legacy=False)
            if "mixtral" in llm_name.lower() or "mistral" in llm_name.lower():
                self.tokenizer.chat_template = open('../templates/mistral-instruct.jinja').read().replace('    ', '').replace('\n', '')
                self.max_length = 32768
            elif "llama-2" in llm_name.lower():
                self.max_length = 4096
                self.type = torch.float16
            elif "llama-3" in llm_name.lower():
                self.max_length = 8192
            elif "meditron-70b" in llm_name.lower():
                self.tokenizer.chat_template = open('../templates/meditron.jinja').read().replace('    ', '').replace('\n', '')
                self.max_length = 4096
            elif "pmc_llama" in llm_name.lower():
                self.tokenizer.chat_template = open('../templates/pmc_llama.jinja').read().replace('    ', '').replace('\n', '')
                self.max_length = 2048
            self.model = transformers.pipeline(
                "text-generation",
                model=self.llm_name,
                torch_dtype=self.type,
                device_map="auto",
                model_kwargs={"cache_dir":self.cache_dir},
            )

    def answer(self, messages):
        # generate answers

        ans = self.generate(messages)
        ans = re.sub("\s+", " ", ans)
        return ans

    def custom_stop(self, stop_str, input_len=0):
        stopping_criteria = StoppingCriteriaList([CustomStoppingCriteria(stop_str, self.tokenizer, input_len)])
        return stopping_criteria
    

    def get_result(self, instruction, text, model, mcp):
        if mcp:
            fast = FastAgent("fast-agent example")

            @fast.agent(instruction=instruction, model=model, servers=["medcalc"])
            async def agent_function():
                async with fast.run() as agent:
                    result = await agent(text)
                    return result

            loop = asyncio.get_event_loop()
            return loop.run_until_complete(agent_function())

        else:
            fast = FastAgent("fast-agent example")

            @fast.agent(instruction=instruction, model=model, servers=[])
            async def agent_function():
                async with fast.run() as agent:
                    result = await agent(text)
                    return result

            loop = asyncio.get_event_loop()
            return loop.run_until_complete(agent_function())

    def to_dict(self, function_name, result):
        if isinstance(result, dict):
            return result
        else:
            return {function_name: result}

    def gen(self, func):
        sig = inspect.signature(func)
        params = sig.parameters
        doc = inspect.getdoc(func)

        # Parse parameter descriptions from docstring
        param_docs = {}
        if doc:
            lines = doc.splitlines()
            try:
                param_index = lines.index("Parameters:") + 1
                for line in lines[param_index:]:
                    if line.strip() == "":
                        break
                    if ':' in line:
                        name, desc = line.strip().split(":", 1)
                        param_docs[name.strip()] = desc.strip()
            except ValueError:
                pass

        # Build OpenAI-compatible schema
        schema = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": doc.split("\n")[0] if doc else "",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

        type_map = {
            int: "integer",
            float: "number",
            bool: "boolean",
            str: "string"
        }

        hints = get_type_hints(func)
        for name, param in params.items():
            param_type = hints.get(name, str)
            schema["function"]["parameters"]["properties"][name] = {
                "type": type_map.get(param_type, "string"),
                "description": param_docs.get(name, "")
            }
            if param.default is inspect.Parameter.empty:
                schema["function"]["parameters"]["required"].append(name)

        return schema


    def generate(self, messages, prompt=None):
        '''
        generate response given messages
        '''
        if "mcp" in self.llm_name.lower():
            model = None
            mcp = False
            if "haiku" in self.llm_name.lower():
                model = 'haiku'
            if "sonnet" in self.llm_name.lower():
                model = 'sonnet'
            if "gpt-4.1" in self.llm_name.lower():
                model = 'gpt-4.1-mini'
            if "o1" in self.llm_name.lower():
                model = 'o1'
            if "gpt-4o" in self.llm_name.lower():
                model = 'gpt-4o'
            if "o1-mini" in self.llm_name.lower():
                model = 'o1-mini'
            if "o3-mini" in self.llm_name.lower():
                model = 'o3-mini'
            
            if "true" in self.llm_name.lower():
                mcp = True

            if model is None:
                raise ValueError("Model not found")
            instruction = messages[0]["content"]
            text = messages[1]["content"]
        
            ans = self.get_result(instruction, text, model, mcp)

        elif "tools" in self.llm_name.lower():
            if "openai" in self.llm_name.lower():
                client = openai.OpenAI()
                
                # Define your tools/functions
                # tools = [
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "egfr_epi",
                #             "description": "Estimated Glomerular Filtration Rate (eGFR) using the EPI formula (version 2021)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "scr": {
                #                         "type": "number",
                #                         "description": "serum creatinine level in mg/dL"
                #                     },
                #                     "age": {
                #                         "type": "integer",
                #                         "description": "Age in years"
                #                     },
                #                     "male": {
                #                         "type": "boolean",
                #                         "description": "true if Male"
                #                     },
                #                 },
                #                 "required": ["scr", "age", "male"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "crcl_cockcroft_gault",
                #             "description": "Calculate Creatinine Clearance using the Cockcroft-Gault formula",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age": {
                #                         "type": "integer",
                #                         "description": "Age in years"
                #                     },
                #                     "weight": {
                #                         "type": "number",
                #                         "description": "Actual body weight in kg"
                #                     },
                #                     "height": {
                #                         "type": "number",
                #                         "description": "Height in inches"
                #                     },
                #                     "scr": {
                #                         "type": "number",
                #                         "description": "serum creatinine level in mg/dL"
                #                     },
                #                     "sex": {
                #                         "type": "string",
                #                         "description": "Gender ('male' or 'female')"
                #                     },
                #                 },
                #                 "required": ["age", "weight", "height", "scr", "sex"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "egfr_epi_cr_cys",
                #             "description": "Estimated Glomerular Filtration Rate (eGFR) using the 2021 CKD-EPI Creatinine-Cystatin C equation",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "scr": {
                #                         "type": "number",
                #                         "description": "Serum creatinine level in mg/dL"
                #                     },
                #                     "scys": {
                #                         "type": "number",
                #                         "description": "Serum cystatin C level in mg/L"
                #                     },
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "male": {
                #                         "type": "boolean",
                #                         "description": "True if patient is male"
                #                     }
                #                 },
                #                 "required": ["scr", "scys", "age", "male"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "mdrd_gfr",
                #             "description": "Estimates GFR in CKD patients using creatinine and patient characteristics",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "scr": {
                #                         "type": "number",
                #                         "description": "Serum creatinine level in mg/dL"
                #                     },
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "is_black": {
                #                         "type": "boolean",
                #                         "description": "True if patient is black"
                #                     },
                #                     "is_female": {
                #                         "type": "boolean",
                #                         "description": "True if patient is female"
                #                     }
                #                 },
                #                 "required": ["scr", "age", "is_black", "is_female"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "bp_children",
                #             "description": "Calculate blood pressure percentiles for children based on age, height, sex, and measured BP",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "years": {
                #                         "type": "integer",
                #                         "description": "Age in years"
                #                     },
                #                     "months": {
                #                         "type": "integer",
                #                         "description": "Additional age in months"
                #                     },
                #                     "height": {
                #                         "type": "integer",
                #                         "description": "Height in cm"
                #                     },
                #                     "sex": {
                #                         "type": "string",
                #                         "description": "Gender ('male' or 'female')"
                #                     },
                #                     "systolic": {
                #                         "type": "integer",
                #                         "description": "Systolic blood pressure (mmHg)"
                #                     },
                #                     "diastolic": {
                #                         "type": "integer",
                #                         "description": "Diastolic blood pressure (mmHg)"
                #                     }
                #                 },
                #                 "required": ["years", "months", "height", "sex", "systolic", "diastolic"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "bmi_calculator",
                #             "description": "Calculates Body Mass Index (BMI)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "weight": {
                #                         "type": "number",
                #                         "description": "Weight in kilograms"
                #                     },
                #                     "height": {
                #                         "type": "number",
                #                         "description": "Height in centimeters"
                #                     },
                #                 },
                #                 "required": ["weight", "height"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "bsa_calculator",
                #             "description": "Calculates Body Surface Area (BSA)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "weight": {
                #                         "type": "number",
                #                         "description": "Weight in kilograms"
                #                     },
                #                     "height": {
                #                         "type": "number",
                #                         "description": "Height in centimeters"
                #                     },
                #                 },
                #                 "required": ["weight", "height"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "map_calculator",
                #             "description": "Calculate Mean Arterial Pressure (MAP)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "sbp": {
                #                         "type": "number",
                #                         "description": "Systolic Blood Pressure in mmHg"
                #                     },
                #                     "dbp": {
                #                         "type": "number",
                #                         "description": "Diastolic Blood Pressure in mmHg"
                #                     }
                #                 },
                #                 "required": ["sbp", "dbp"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "chads2_vasc_score",
                #             "description": "Calculate CHA₂DS₂-VASc Score for Atrial Fibrillation Stroke Risk",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age": { "type": "integer", "description": "Age in years" },
                #                     "female": { "type": "boolean", "description": "True if patient is female" },
                #                     "chf": { "type": "boolean", "description": "History of congestive heart failure" },
                #                     "hypertension": { "type": "boolean", "description": "History of hypertension" },
                #                     "stroke_history": { "type": "boolean", "description": "History of stroke, TIA, or thromboembolism" },
                #                     "vascular_disease": { "type": "boolean", "description": "History of vascular disease" },
                #                     "diabetes": { "type": "boolean", "description": "History of diabetes mellitus" }
                #                 },
                #                 "required": ["age", "female", "chf", "hypertension", "stroke_history", "vascular_disease", "diabetes"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #         "name": "prevent_cvd_risk",
                #         "description": "Predicts 10-year cardiovascular disease risk for patients aged 30-79 without known CVD.",
                #         "parameters": {
                #             "type": "object",
                #             "properties": {
                #             "age": { "type": "integer", "description": "Age in years (30-79)" },
                #             "female": { "type": "boolean", "description": "True if patient is female, False if male" },
                #             "tc": { "type": "number", "description": "Total cholesterol in mmol/L" },
                #             "hdl": { "type": "number", "description": "HDL cholesterol in mmol/L" },
                #             "sbp": { "type": "integer", "description": "Systolic blood pressure in mmHg" },
                #             "diabetes": { "type": "boolean", "description": "True if patient has diabetes" },
                #             "current_smoker": { "type": "boolean", "description": "True if patient is a current smoker" },
                #             "egfr": { "type": "number", "description": "Estimated GFR in mL/min/1.73m²" },
                #             "using_antihtn": { "type": "boolean", "description": "True if using antihypertensive drugs" },
                #             "using_statins": { "type": "boolean", "description": "True if using statins" }
                #             },
                #             "required": [
                #             "age", "female", "tc", "hdl", "sbp", "diabetes", 
                #             "current_smoker", "egfr", "using_antihtn", "using_statins"
                #             ]
                #         }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #         "name": "corrected_calcium",
                #         "description": "Calculates corrected serum calcium based on albumin levels.",
                #         "parameters": {
                #             "type": "object",
                #             "properties": {
                #                 "serum_calcium": { "type": "number", "description": "Measured serum calcium in mg/dL" },
                #                 "patient_albumin": { "type": "number", "description": "Measured albumin level in g/dL" },
                #             },
                #             "required": ["serum_calcium", "patient_albumin"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #         "name": "qtc_calculator",
                #         "description": "Calculates the corrected QT (QTc) interval using multiple formula options.",
                #         "parameters": {
                #             "type": "object",
                #             "properties": {
                #             "qt_interval": { "type": "number", "description": "QT interval in milliseconds" },
                #             "heart_rate": { "type": "number", "description": "Heart rate in bpm" },
                #             "formula": {
                #                 "type": "string",
                #                 "enum": ["bazett", "fridericia", "framingham", "hodges", "rautaharju"],
                #                 "default": "bazett",
                #                 "description": "Formula to use for QTc correction"
                #             }
                #             },
                #             "required": ["qt_interval", "heart_rate"]
                #         }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #         "name": "wells_pe_criteria",
                #         "description": "Calculate Wells Criteria for Pulmonary Embolism (PE)",
                #         "parameters": {
                #             "type": "object",
                #             "properties": {
                #             "clinical_signs_dvt": { "type": "boolean", "description": "QT interval in milliseconds" },
                #             "alternative_diagnosis_less_likely": { "type": "boolean", "description": "Alternative diagnosis less likely than PE" },
                #             "heart_rate_over_100": { "type": "boolean", "description": "Heart rate > 100 beats per minute" },
                #             "immobilization_or_surgery": { "type": "boolean", "description": "Recent immobilization or surgery" },
                #             "previous_dvt_pe": { "type": "boolean", "description": "Previous DVT or PE" },
                #             "hemoptysis": { "type": "boolean", "description": "Hemoptysis" },
                #             "malignancy": { "type": "boolean", "description": "Active malignancy" },
                #             },
                #             "required": ["clinical_signs_dvt", "alternative_diagnosis_less_likely", "heart_rate_over_100", "immobilization_or_surgery", "previous_dvt_pe", "hemoptysis", "malignancy"]
                #         }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "nihss_score",
                #             "description": "Calculate NIH Stroke Scale (NIHSS) score",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "loc_alert": { 
                #                         "type": "number",
                #                         "description": "Level of consciousness (LOC) alertness score (0-3)"
                #                     },
                #                     "loc_respond": { 
                #                         "type": "number",
                #                         "description": "Level of consciousness (LOC) response score (0-2)"
                #                     },
                #                     "loc_commands": { 
                #                         "type": "number",
                #                         "description": "Level of consciousness (LOC) commands score (0-2)"
                #                     },
                #                     "best_gaze": { 
                #                         "type": "number",
                #                         "description": "Best gaze score (0-2)"
                #                     },
                #                     "visual_field": { 
                #                         "type": "number",
                #                         "description": "Visual field score (0-3)"
                #                     },
                #                     "facial_palsy": { 
                #                         "type": "number",
                #                         "description": "Facial palsy score (0-3)"
                #                     },
                #                     "motor_arm_left": { 
                #                         "type": "number",
                #                         "description": "Motor arm score (0-4)"
                #                     },                                    
                #                     "motor_arm_right": { 
                #                         "type": "number",
                #                         "description": "Motor arm score (0-4)"
                #                     },
                #                     "motor_leg_left": { 
                #                         "type": "number",
                #                         "description": "Motor leg score (0-4)"
                #                     },
                #                      "motor_leg_right": { 
                #                         "type": "number",
                #                         "description": "Motor leg score (0-4)"
                #                     },
                #                     "limb_ataxia": { 
                #                         "type": "number",
                #                         "description": "Limb ataxia score (0-2)"
                #                     },
                #                     "sensory": { 
                #                         "type": "number",
                #                         "description": "Sensory score (0-2)"
                #                     },
                #                     "best_language": { 
                #                         "type": "number",
                #                         "description": "Best language score (0-3)"
                #                     },
                #                     "dysarthria": { 
                #                         "type": "number",
                #                         "description": "Dysarthria score (0-2)"
                #                     },
                #                     "extinction_inattention": { 
                #                         "type": "number",
                #                         "description": "Extinction and inattention score (0-2)"
                #                     },
                #                 },
                #                 "required": ["loc_alert", "loc_respond", "loc_commands", "best_gaze", "visual_field", "facial_palsy", "motor_arm_left", "motor_arm_right", "motor_leg_left", "motor_leg_right", "limb_ataxia", "sensory", "best_language", "dysarthria", "extinction_inattention"]                            
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "ibw_calculator",
                #             "description": "Calculate ibw (ideal body weight)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "weight_kg": {
                #                         "type": "number",
                #                         "description": "Actual body weight in kilograms"
                #                     },
                #                     "height_cm": {
                #                         "type": "number",
                #                         "description": "Height in centimeters"
                #                     },
                #                     "male"  : {
                #                         "type": "boolean",
                #                         "description": "True if male"
                #                     }
                #                 },
                #                 "required": ["weight_kg", "height_cm","male"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "abw_calculator",
                #             "description": "Calculate abw (adjusted body weight)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "weight_kg": {
                #                         "type": "number",
                #                         "description": "Actual body weight in kilograms"
                #                     },
                #                     "height_cm": {
                #                         "type": "number",
                #                         "description": "Height in centimeters"
                #                     },
                #                     "male"  : {
                #                         "type": "boolean",
                #                         "description": "True if male"
                #                     }
                #                 },
                #                 "required": ["weight_kg", "height_cm","male"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "pregnancy_calculator",
                #             "description": "Calculate estimated due date based on last menstrual period (LMP)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "calculation_method":{
                #                         "type": "string",
                #                         "description": "Method used for calculation: 'lmp' (last menstrual period), 'conception', or 'ultrasound'"
                #                     },
                #                     "date_value": {
                #                         "type": "string",
                #                         "description": "Date in YYYY-MM-DD format (date of LMP, conception, or ultrasound)" 
                #                     },
                #                     "cycle_length": {
                #                         "type": "number",
                #                         "description": "Length of menstrual cycle in days"
                #                     },
                #                     "gestational_age_weeks": {
                #                         "type": "number",
                #                         "description": "Gestational age in weeks (required if calculation_method is 'ultrasound')"
                #                     },
                #                     "gestational_age_days": {
                #                         "type": "number",
                #                         "description": "Gestational age in days (required if calculation_method is 'ultrasound')"
                #                     },
                #                 },
                #                 "required": ["calculation_method", "date_value", "cycle_length"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "revised_cardiac_risk_index",
                #             "description": "Estimates risk of cardiac complications after noncardiac surgery",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "high_risk_surgery":{
                #                         "type": "boolean",
                #                         "description": "Intraperitoneal, intrathoracic, or suprainguinal vascular surgery"
                #                     },
                #                     "ischemic_heart_disease": {
                #                         "type": "boolean",
                #                         "description": "History of MI, positive exercise test, current chest pain considered due to myocardial ischemia, use of nitrate therapy, or ECG with pathological Q waves" 
                #                     },
                #                     "congestive_heart_failure": {
                #                         "type": "boolean",
                #                         "description": "Pulmonary edema, bilateral rales, S3 gallop, paroxysmal nocturnal dyspnea, or CXR showing pulmonary vascular redistribution"
                #                     },
                #                     "cerebrovascular_disease": {
                #                         "type": "boolean",
                #                         "description": "Prior transient ischemic attack (TIA) or stroke"
                #                     },
                #                     "insulin_treatment": {
                #                         "type": "boolean",
                #                         "description": "Pre-operative treatment with insulin"
                #                     },                                    
                #                     "creatinine_over_2mg": {
                #                         "type": "boolean",
                #                         "description": "Pre-operative creatinine >2 mg/dL (176.8 µmol/L)"
                #                     },
                #                 },
                #                 "required": ["high_risk_surgery", "ischemic_heart_disease", "congestive_heart_failure", "cerebrovascular_disease", "insulin_treatment", "creatinine_over_2mg"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "child_pugh_score",
                #             "description": "Calculates the Child-Pugh Score for cirrhosis mortality assessment",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "bilirubin": {
                #                         "type": "number",
                #                         "description": "Serum bilirubin level in mg/dL"
                #                     },
                #                     "albumin": {
                #                         "type": "number",
                #                         "description": "Serum albumin level in g/dL"
                #                     },
                #                     "ascites": {
                #                         "type": "string",
                #                         "description": "Ascites severity: 'absent', 'slight', or 'moderate'"
                #                     },
                #                     "inr": {
                #                         "type": "number",
                #                         "description": "International Normalized Ratio (INR) for prothrombin time."
                #                     },
                #                     "encephalopathy_grade": {
                #                         "type": "number",
                #                         "description": "Hepatic encephalopathy grade: 0 (none), 1-2 (mild), 3-4 (severe)."
                #                     }
                #                 },
                #                 "required": ["bilirubin", "albumin", "ascites", "inr", "encephalopathy_grade"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "phq9_score",
                #             "description": "PHQ-9 (Patient Health Questionnaire-9), Objectifies degree of depression severity.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "interest": {
                #                         "type": "number",
                #                         "description": "Little interest or pleasure in doing things (0-3)"
                #                     },
                #                     "depressed": {
                #                         "type": "number",
                #                         "description": "Feeling down, depressed, or hopeless (0-3)"
                #                     },
                #                     "sleep": {
                #                         "type": "number",
                #                         "description": "Trouble falling asleep, staying asleep, or sleeping too much (0-3)"
                #                     },
                #                     "tired": {
                #                         "type": "number",
                #                         "description": "Feeling tired or having little energy (0-3)"
                #                     },
                #                     "appetite": {
                #                         "type": "number",
                #                         "description": "Poor appetite or overeating (0-3)"
                #                     },
                #                     "feeling_bad": {
                #                         "type": "number",
                #                         "description": "Feeling bad about yourself or that you are a failure (0-3)"
                #                     },
                #                     "concentration": {
                #                         "type": "number",
                #                         "description": "Trouble concentrating on things (0-3)"
                #                     },
                #                     "movement":{
                #                         "type": "number",
                #                         "description": "Moving or speaking so slowly that other people could have noticed (0-3)"
                #                     },
                #                     "self_harm": {
                #                         "type": "number",
                #                         "description": "Thoughts that you would be better off dead or hurting yourself (0-3)"
                #                     },
                #                 },
                #                 "required": ["interest", "depressed", "sleep", "tired", "appetite", "feeling_bad", "concentration", "movement", "self_harm"]
                #             }
                #         }
                #     },

                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "heart_score",
                #             "description": "HEART Score for Major Cardiac Events",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "history": {
                #                         "type": "number",
                #                         "description": "Patient history rating (0: Slightly suspicious, 1: Moderately suspicious, 2: Highly suspicious)"
                #                     },
                #                     "ekg": {
                #                         "type": "number",
                #                         "description": "ECG findings rating (0: Normal, 1: Non-specific repolarization disturbance, 2: Significant ST deviation)"
                #                     },
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "risk_factors": {
                #                         "type": "number",
                #                         "description": "Risk factors rating (0: No risk factors, 1: 1-2 risk factors, 2: 3 or more risk factors)"
                #                     },
                #                     "troponin": {
                #                         "type": "number",
                #                         "description": "Initial troponin level (0: ≤normal limit, 1: 1-3× normal limit, 2: >3× normal limit)"
                #                     }
                #                 },
                #                 "required": ["history", "ekg", "age", "risk_factors", "troponin"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "stop_bang_score",
                #             "description": "STOP-BANG Score for Obstructive Sleep Apnea, Screens for obstructive sleep apnea.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "snoring": {
                #                         "type": "boolean",
                #                         "description": "Do you snore loudly (loud enough to be heard through closed doors)?"
                #                     },
                #                     "tired": {
                #                         "type": "boolean",
                #                         "description": "Do you often feel tired, fatigued, or sleepy during the daytime?"
                #                     },
                #                     "observed_apnea": {
                #                         "type": "boolean",
                #                         "description": "Has anyone observed you stop breathing during your sleep?"
                #                     },
                #                     "bp_high": {
                #                         "type": "boolean",
                #                         "description": "Do you have or are you being treated for high blood pressure?"
                #                     },
                #                     "bmi_over_35": {
                #                         "type": "boolean",
                #                         "description": "Is your body mass index (BMI) more than 35 kg/m²?"
                #                     },
                #                     "age_over_50": {
                #                         "type": "boolean",
                #                         "description": "Are you older than 50 years?"
                #                     },
                #                     "neck_over_40cm": {
                #                         "type": "boolean",
                #                         "description": "Is your neck circumference more than 40 cm (15.75 inches)?"
                #                     },
                #                     "male": {
                #                         "type": "boolean",
                #                         "description": "Is patient male?"
                #                     },

                #                 },
                #                 "required": ["snoring", "tired", "observed_apnea", "bp_high", "bmi_over_35", "age_over_50", "neck_over_40cm", "male"]
                #             },
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "steroid_conversion",
                #             "description": "Converts corticosteroid dosages using standard equivalencies",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "from_steroid": {
                #                         "type": "string",
                #                         "description": "Name of the original steroid (e.g., 'prednisone', 'dexamethasone')."
                #                     },
                #                     "from_dose_mg": {
                #                         "type": "number",
                #                         "description": "Dose of the original steroid in mg"
                #                     },
                #                     "to_steroid": {
                #                         "type": "string",
                #                         "description": "Name of the steroid to convert to."
                #                     }
                #                 },
                #                 "required": ["from_steroid", "from_dose_mg", "to_steroid"]
                #             }
                #         }
                #     },                    
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "calculate_mme",
                #             "description": "Calculate morphine milligram equivalents (MME) for opioid conversion",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "opioid": {
                #                         "type": "string",
                #                         "description": "Name of the original steroid (e.g., 'prednisone', 'dexamethasone')."
                #                     },
                #                     "dose_per_administration": {
                #                         "type": "number",
                #                         "description": "Amount of opioid per dose (mg for most, mcg/hr for fentanyl patch)"
                #                     },
                #                     "doses_per_day": {
                #                         "type": "number",
                #                         "description": "Number of times the dose is taken per day"
                #                     }
                #                 },
                #                 "required": ["opioid", "dose_per_administration", "doses_per_day"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "maintenance_fluids",
                #             "description": "Calculates maintenance IV fluid rate (mL/hr) using the 4-2-1 Rule.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "weight_kg": {
                #                         "type": "number",
                #                         "description": "Patient's weight in kilograms"
                #                     },
                #                 },
                #                 "required": ["weight_kg"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "correctedsodiumkatz",
                #             "description": "Calculates corrected sodium level in the setting of hyperglycemia using Katz correction formulas",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "measured_sodium": {
                #                         "type": "number",
                #                         "description": "Measured serum sodium in mEq/L"
                #                     },
                #                     "serum_glucose": {
                #                         "type": "number",
                #                         "description": "Serum glucose in mg/dL"
                #                     },
                #                 },
                #                 "required": ["measured_sodium", "serum_glucose"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "correctedsodiumhillier",
                #             "description": "Calculates corrected sodium level in the setting of hyperglycemia using Hillier correction formulas",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "measured_sodium": {
                #                         "type": "number",
                #                         "description": "Measured serum sodium in mEq/L"
                #                     },
                #                     "serum_glucose": {
                #                         "type": "number",
                #                         "description": "Serum glucose in mg/dL"
                #                     },
                #                 },
                #                 "required": ["measured_sodium", "serum_glucose"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "has_bled_score",
                #             "description": "HAS-BLED Score for Major Bleeding Risk, estimates risk of major bleeding for patients on anticoagulation to assess risk-benefit in atrial fibrillation care.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "hypertension": {
                #                         "type": "boolean",
                #                         "description": "Uncontrolled hypertension (systolic BP > 160 mmHg)"
                #                     },
                #                     "abnormal_renal_function": {
                #                         "type": "boolean",
                #                         "description": "Renal disease (dialysis, transplant, Cr >2.26 mg/dL or 200 µmol/L)"
                #                     },
                #                     "abnormal_liver_function": {
                #                         "type": "boolean",
                #                         "description": "Liver disease (cirrhosis or bilirubin >2x normal with AST/ALT/AP >3x normal)"
                #                     },
                #                     "stroke_history": {
                #                         "type": "boolean",
                #                         "description": "History of stroke"
                #                     },
                #                     "bleeding_history": {
                #                         "type": "boolean",
                #                         "description": "History of bleeding"
                #                     },
                #                     "labile_inr": {
                #                         "type": "boolean",
                #                         "description": "Labile INR (e.g., frequent changes in INR)"
                #                     },
                #                     "elderly": {
                #                         "type": "boolean",
                #                         "description": "Age over 65 years"
                #                     },
                #                     "drugs": {
                #                         "type": "boolean",
                #                         "description": "True if using drugs"
                #                     },
                #                     "alcohol": {
                #                         "type": "boolean",
                #                         "description": "True if using alcohols"
                #                     }
                #                 },
                #                 "required": ["hypertension", "abnormal_renal_function", "abnormal_liver_function", "stroke_history", "bleeding_history", "labile_inr", "elderly", "drugs", "alcohol"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "centor_score_modified",
                #             "description": "Modified Centor Score for Strep Throat, estimates risk of streptococcal pharyngitis.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age":{
                #                         "type": "number",
                #                         "description": "Age of the patient in years"
                #                     },
                #                     "tonsillar_exudate": {
                #                         "type": "boolean",
                #                         "description": "Presence of tonsillar exudate"
                #                     },
                #                     "swollen_lymph_nodes": {
                #                         "type": "boolean",
                #                         "description": "Tender/swollen anterior cervical lymph nodes"
                #                     },
                #                     "fever": {
                #                         "type": "boolean",
                #                         "description": "Fever over 100.4°F (38°C)"
                #                     },
                #                     "cough_absent": {
                #                         "type": "boolean",
                #                         "description": "Absence of cough"
                #                     },
                #                 },
                #                 "required": ["age", "tonsillar_exudate", "swollen_lymph_nodes", "fever", "cough_absent"]
                #             }
                #         },
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "glasgow_coma_scale",
                #             "description": "Calculates the Glasgow Coma Scale (GCS) score based on eye, verbal, and motor responses. Eye Opening (E): 4 = Spontaneous 3 = To verbal command 2 = To pain 1 = No eye opening NT = Not testable (not scored) Verbal Response (V): 5 = Oriented 4 = Confused conversation 3 = Inappropriate words 2 = Incomprehensible sounds 1 = No verbal response NT = Not testable (e.g., intubated; not scored) Motor Response (M): 6 = Obeys commands 5 = Localizes to pain 4 = Withdraws from pain 3 = Flexion to pain (decorticate) 2 = Extension to pain (decerebrate) 1 = No motor response NT = Not testable (e.g., paralyzed; not scored)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "eye_response": {
                #                         "type": "number",
                #                         "description": "Eye response score (1-4)"
                #                     },
                #                     "verbal_response": {
                #                         "type": "number",
                #                         "description": "Verbal response score (1-5)"
                #                     },
                #                     "motor_response": {
                #                         "type": "number",
                #                         "description": "Motor response score (1-6)"
                #                     }
                #                 },
                #                 "required": ["eye_response", "verbal_response", "motor_response"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "caprini_score",
                #             "description": "Calculates the Caprini score for venous thromboembolism (VTE) risk assessment",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "sex": {
                #                         "type": "string",
                #                         "description": "'male' or 'female'"
                #                     },
                #                     "surgery_type": {
                #                         "type": "string",
                #                         "description": "Type of surgery ('none', 'minor', 'major', 'arthroplasty')"
                #                     },
                #                     "recent_major_surgery": {
                #                         "type": "boolean",
                #                         "description": "True if patient had major surgery in the last 30 days"
                #                     },
                #                     "chf": {
                #                         "type": "boolean",
                #                         "description": "True if patient has congestive heart failure"
                #                     },
                #                     "sepsis": {
                #                         "type": "boolean",
                #                         "description": "True if patient has a history of stroke"
                #                     },
                #                     "pneumonia": {
                #                         "type": "boolean",
                #                         "description": "True if patient has pneumonia"
                #                     },
                #                     "immobilizing_cast": {
                #                         "type": "boolean",
                #                         "description": "True if patient has an immobilizing cast"
                #                     },
                #                     "fracture": {
                #                         "type": "boolean",
                #                         "description": "True if patient has a fracture"
                #                     },
                #                     "stroke": {
                #                         "type": "boolean",
                #                         "description": "True if patient has a history of stroke"
                #                     },
                #                     "multiple_trauma": {
                #                         "type": "boolean",
                #                         "description": "True if patient has multiple trauma"
                #                     },
                #                     "spinal_cord_injury": {
                #                         "type": "boolean",
                #                         "description": "True if patient has spinal cord injury"
                #                     },
                #                     "varicose_veins": {
                #                         "type": "boolean",
                #                         "description": "True if patient has varicose veins"
                #                     },
                #                     "swollen_legs": {
                #                         "type": "boolean",
                #                         "description": "True if patient has swollen legs"
                #                     },
                #                     "central_venous_access":{
                #                         "type": "boolean",
                #                         "description": "True if patient has central venous access"
                #                     },
                #                     "history_dvt_pe": {
                #                         "type": "boolean",
                #                         "description": "True if patient has a history of deep vein thrombosis (DVT) or pulmonary embolism (PE)"
                #                     },
                #                     "family_history_thrombosis": {
                #                         "type": "boolean",
                #                         "description": "True if patient has a family history of thrombosis"
                #                     },
                #                     "factor_v_leiden": {
                #                         "type": "boolean",
                #                         "description": "True if patient has factor V Leiden mutation"
                #                     },
                #                     "prothrombin_20210a": {
                #                         "type": "boolean",
                #                         "description": "True if patient has prothrombin G20210A mutation"
                #                     },
                #                     "homocysteine": {
                #                         "type": "boolean",
                #                         "description": "True if patient has elevated homocysteine levels"
                #                     },
                #                     "lupus_anticoagulant": {
                #                         "type": "boolean",
                #                         "description": "True if patient has lupus anticoagulant"
                #                     },
                #                     "anticardiolipin_antibody": {
                #                         "type": "boolean",
                #                         "description": "True if patient has anticardiolipin antibody"
                #                     },
                #                     "hit": {
                #                         "type": "boolean",
                #                         "description": "True if patient has heparin-induced thrombocytopenia (HIT)"
                #                     },
                #                     "other_thrombophilia": {
                #                         "type": "boolean",
                #                         "description": "True if patient has other thrombophilia"
                #                     },
                #                     "mobility_status": {
                #                         "type": "string",
                #                         "description": "Mobility status (one of 'normal', 'bedrest', 'bedrest_72hr')"
                #                     },
                #                     "ibd": {
                #                         "type": "boolean",
                #                         "description": "True if patient has inflammatory bowel disease (IBD)"
                #                     },
                #                     "bmi_over_25": {
                #                         "type": "boolean",
                #                         "description": "True if patient has a body mass index (BMI) over 25"
                #                     },
                #                     "acute_mi": {
                #                         "type": "boolean",
                #                         "description": "True if patient has had an acute myocardial infarction (MI)"
                #                     },
                #                     "copd": {
                #                         "type": "boolean",
                #                         "description": "True if patient has chronic obstructive pulmonary disease (COPD)"
                #                     },
                #                     "malignancy": {
                #                         "type": "boolean",
                #                         "description": "True if patient has malignancy"
                #                     },
                #                     "other_risk_factors": {
                #                         "type": "boolean",
                #                         "description": "True if patient has other risk factors for VTE"
                #                     }

                #                 },
                #                 "required": ["age","sex","surgery_type","recent_major_surgery","chf","sepsis","pneumonia","immobilizing_cast","fracture","stroke","multiple_trauma","spinal_cord_injury","varicose_veins","swollen_legs","central_venous_access","history_dvt_pe","family_history_thrombosis","factor_v_leiden","prothrombin_20210a","homocysteine","lupus_anticoagulant","anticardiolipin_antibody","hit","other_thrombophilia","mobility_status","ibd","bmi_over_25","acute_mi","copd","malignancy","other_risk_factors"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "ldl_calculated",
                #             "description": "Calculates LDL cholesterol using the Friedewald equation",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "total_cholesterol": {
                #                         "type": "number",
                #                         "description": "Total cholesterol in mg/dL"
                #                     },
                #                     "hdl": {
                #                         "type": "number",
                #                         "description": "HDL cholesterol in mg/dL"
                #                     },
                #                     "triglycerides": {
                #                         "type": "number",
                #                         "description": "Triglycerides in mg/dL"
                #                     },
                #                 },
                #                 "required": ["total_cholesterol", "hdl", "triglycerides"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "sofa_score",
                #             "description": "Calculates the SOFA score for assessing organ dysfunction in sepsis",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "pao2_fio2": {
                #                         "type": "number",
                #                         "description": "PaO2/FiO2 ratio"
                #                     },
                #                     "mechanically_ventilated": {
                #                         "type": "boolean",
                #                         "description": "True if patient is mechanically ventilated"
                #                     },
                #                     "platelets": {
                #                         "type": "number",
                #                         "description": "Platelet count in Platelet count in ×10³/µL"
                #                     },
                #                     "gcs": {
                #                         "type": "number",
                #                         "description": "Glasgow Coma Scale (GCS) score"
                #                     },
                #                     "bilirubin": {
                #                         "type": "number",
                #                         "description": "Serum bilirubin in mg/dL"
                #                     },
                #                     "map_mmHg": {
                #                         "type": "number",
                #                         "description": "Mean arterial pressure (MAP) in mmHg"
                #                     },
                #                     "dopamine": {
                #                         "type": "number",
                #                         "description": "Dopamine dose in µg/kg/min"
                #                     },
                #                     "dobutamine": {
                #                         "type": "number",
                #                         "description": "Dobutamine dose in µg/kg/min"
                #                     },
                #                     "epinephrine": {
                #                         "type": "number",
                #                         "description": "Epinephrine dose in µg/kg/min"
                #                     },
                #                     "norepinephrine": {
                #                         "type": "number",
                #                         "description": "Norepinephrine dose in µg/kg/min"
                #                     },
                #                     "creatinine": {
                #                         "type": "number",
                #                         "description": "Serum creatinine in mg/dL"
                #                     },
                #                     "urine_output": {
                #                         "type": "number",
                #                         "description": "Urine output in mL/day"
                #                     },
                #                 },
                #                 "required": ["pao2_fio2", "mechanically_ventilated", "platelets", "gcs", "bilirubin", "map_mmHg", "dopamine", "dobutamine", "epinephrine", "norepinephrine", "creatinine", "urine_output"]
                #             }
                #         }
                #     },

                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "perc_rule",
                #             "description": "PERC Rule for Pulmonary Embolism. Rules out PE in low-risk patients if **none** of the criteria are present.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age_over_50": {
                #                         "type": "boolean",
                #                         "description": "True if over 50 years"
                #                     },
                #                     "heart_rate_100_or_more": {
                #                         "type": "boolean",
                #                         "description": "True if Heart rate over 100 beats per minute"
                #                     },
                #                     "oxygen_sat_below_95": {
                #                         "type": "boolean",
                #                         "description": "True if Oxygen saturation below 95%"
                #                     },
                #                     "unilateral_leg_swelling": {
                #                         "type": "boolean",
                #                         "description": "True if Unilateral leg swelling"
                #                     },
                #                     "hemoptysis": {
                #                         "type": "boolean",
                #                         "description": "True if Hemoptysis (coughing up blood)"
                #                     },
                #                     "recent_trauma_or_surgery": {
                #                         "type": "boolean",
                #                         "description": "True if Recent trauma or surgery"
                #                     },
                #                     "prior_pe_or_dvt": {
                #                         "type": "boolean",
                #                         "description": "True if Prior PE or DVT"
                #                     },
                #                     "hormone_use":{
                #                         "type": "boolean",
                #                         "description": "True if Hormone use (OCPs, HRT, or estrogen)"
                #                     }
                #                 },
                #                 "required": ["age_over_50", "heart_rate_100_or_more", "oxygen_sat_below_95", "unilateral_leg_swelling", "hemoptysis", "recent_trauma_or_surgery", "prior_pe_or_dvt", "hormone_use"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "gad7_score",
                #             "description": "Generalized Anxiety Disorder 7-item (GAD-7) scale for assessing anxiety severity",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "q1": {
                #                         "type": "number",
                #                         "description": "Feeling nervous, anxious, or on edge (0-3)"
                #                     },
                #                     "q2": {
                #                         "type": "number",
                #                         "description": "Not being able to stop or control worrying (0-3)"
                #                     },
                #                     "q3": {
                #                         "type": "number",
                #                         "description": "Worrying too much about different things (0-3)"
                #                     },
                #                     "q4": {
                #                         "type": "number",
                #                         "description": "Trouble relaxing (0-3)"
                #                     },
                #                     "q5": {
                #                         "type": "number",
                #                         "description": "Being so restless that it's hard to sit still (0-3)"
                #                     },
                #                     "q6": {
                #                         "type": "number",
                #                         "description": "Becoming easily annoyed or irritable (0-3)"
                #                     },
                #                     "q7": {
                #                         "type": "number",
                #                         "description": "Feeling afraid as if something awful might happen (0-3)"
                #                     }
                #                 },
                #                 "required": ["q1", "q2", "q3", "q4", "q5", "q6", "q7"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "curb65_score",
                #             "description": "CURB-65 score for assessing the severity of pneumonia and need for hospitalization",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "confusion": {
                #                         "type": "boolean",
                #                         "description": "True if new mental confusion is present"
                #                     },
                #                     "bun_over_19": {
                #                         "type": "boolean",
                #                         "description": "True if BUN > 19 mg/dL (or urea > 7 mmol/L)."
                #                     },
                #                     "respiratory_rate_30_or_more": {
                #                         "type": "boolean",
                #                         "description": "True if respiratory rate is 30 or higher"
                #                     },
                #                     "blood_pressure_low": {
                #                         "type": "boolean",
                #                         "description": "True if SBP < 90 mmHg or DBP ≤ 60 mmHg"
                #                     },
                #                     "age_over_65": {
                #                         "type": "boolean",
                #                         "description": "True if age is 65 years or older"
                #                     }
                #                 },
                #                 "required": ["confusion", "bun_over_19", "respiratory_rate_30_or_more", "blood_pressure_low", "age_over_65"]
                #             }
                #         }

                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "meld_3",
                #             "description": "Calculates MELD-Na score for liver disease severity",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "female": {
                #                         "type": "boolean",
                #                         "description": "True if patient is female"
                #                     },
                #                     "bilirubin": {
                #                         "type": "number",
                #                         "description": "Serum bilirubin in mg/dL"
                #                     },
                #                     "inr": {
                #                         "type": "number",
                #                         "description": "International Normalized Ratio (INR)"
                #                     },
                #                     "creatinine": {
                #                         "type": "number",
                #                         "description": "Serum creatinine in mg/dL"
                #                     },
                #                     "albumin": {
                #                         "type": "number",
                #                         "description": "Serum albumin in g/dL"
                #                     },
                #                     "sodium": {
                #                         "type": "number",
                #                         "description": "Serum sodium in mEq/L"
                #                     },
                #                     "dialysis": {
                #                         "type": "boolean",
                #                         "description": "True if patient is on dialysis"
                #                     },
                #                 },
                #                 "required": ["age","female","bilirubin", "inr", "creatinine", "albumin", "sodium", "dialysis"]
                #             },
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "framingham_risk_score",
                #             "description": "Calculates the Framingham Risk Score for 10-year risk of heart attack (CHD) based on the Framingham Heart Study equation (men and women)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "total_cholesterol": {
                #                         "type": "number",
                #                         "description": "Total cholesterol in mg/dL"
                #                     },
                #                     "hdl_cholesterol": {
                #                         "type": "number",
                #                         "description": "HDL cholesterol in mg/dL"
                #                     },
                #                     "systolic_bp": {
                #                         "type": "number",
                #                         "description": "Systolic blood pressure in mmHg"
                #                     },
                #                     "treated_for_bp": {
                #                         "type": "boolean",
                #                         "description": "True if treated for high blood pressure"
                #                     },
                #                     "smoker": {
                #                         "type": "boolean",
                #                         "description": "True if current smoker"
                #                     },
                #                     "gender": {
                #                         "type": "string",
                #                         "description": "Gender of the patient (male or female)"
                #                     }
                #                 },
                #                 "required": ["age", "total_cholesterol", "hdl_cholesterol", "systolic_bp", "treated_for_bp", "smoker","gender"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "homa_ir",
                #             "description": "Calculates the Homeostasis Model Assessment of Insulin Resistance (HOMA-IR)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "fasting_insulin": {
                #                         "type": "number",
                #                         "description": "Fasting insulin level in micro-units per milliliter (uIU/mL)"
                #                     },                                    
                #                     "fasting_glucose": {
                #                         "type": "number",
                #                         "description": "Fasting insulin level in micro-units per milliliter (uIU/mL)"
                #                     },
                #                 },
                #                 "required": ["fasting_insulin", "fasting_glucose"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "fib4_index",
                #             "description": "Calculates the FIB-4 index for liver fibrosis risk assessment",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "ast": {
                #                         "type": "number",
                #                         "description": "AST level in IU/L"
                #                     },
                #                     "alt": {
                #                         "type": "number",
                #                         "description": "ALT level in IU/L"
                #                     },
                #                     "platelets": {
                #                         "type": "number",
                #                         "description": "Platelet count in 10^9/L"
                #                     }
                #                 },
                #                 "required": ["age", "ast", "alt", "platelets"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "ariscat_score",
                #             "description": "Calculates the ARISCAT score for postoperative pulmonary complications",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "spo2": {
                #                         "type": "number",
                #                         "description": "Oxygen saturation (SpO2) in percentage"
                #                     },
                #                     "recent_respiratory_infection": {
                #                         "type": "boolean",
                #                         "description": "True if patient has a recent respiratory infection"
                #                     },
                #                     "preop_anemia": {
                #                         "type": "boolean",
                #                         "description": "True if patient has preoperative anemia"
                #                     },
                #                     "surgical_site": {
                #                         "type": "string",
                #                         "description": "Surgical site 'peripheral', 'upper_abdominal', or 'intrathoracic'"
                #                     },
                #                     "surgery_duration_hours": {
                #                         "type": "number",
                #                         "description": "Duration of surgery in hours"
                #                     },
                #                     "emergency_surgery": {
                #                         "type": "boolean",
                #                         "description": "True if surgery is an emergency"
                #                     },
                #                 },
                #                 "required": ["age", "spo2", "recent_respiratory_infection", "preop_anemia", "surgical_site", "surgery_duration_hours", "emergency_surgery"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "sepsis_criteria",
                #             "description": "Categorizes patient condition based on systemic inflammatory response and organ function.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "temp_abnormal": {
                #                         "type": "boolean",
                #                         "description": "True if temperature >38°C or <36°C"
                #                     },
                #                     "heart_rate_gt_90": {
                #                         "type": "boolean",
                #                         "description": "True if heart rate >90 beats per minute"
                #                     },
                #                     "rr_gt_20_or_paco2_lt_32": {
                #                         "type": "boolean",
                #                         "description": "True if respiratory rate >20 breaths per minute or PaCO2 <32 mmHg"
                #                     },
                #                     "wbc_abnormal": {
                #                         "type": "boolean",
                #                         "description": "True if WBC >12,000 cells/mm³ or <4,000 cells/mm³ or >10percent immature neutrophils"
                #                     },
                #                     "suspected_infection": {
                #                         "type": "boolean",
                #                         "description": "True if there is a suspected infection"
                #                     },
                #                     "organ_dysfunction": {
                #                         "type": "boolean",
                #                         "description": "True if signs of lactic acidosis or SBP <90 or SBP drop ≥40 mm Hg"
                #                     },
                #                     "fluid_resistant_hypotension": {
                #                         "type": "boolean",
                #                         "destription": "True if hypotension persists despite adequate fluid resuscitation"
                #                     },
                #                     "multi_organ_failure": {
                #                         "type": "boolean",
                #                         "description": "True if there is evidence of multi-organ failure"
                #                     }

                #                 },
                #                 "required": ["temp_abnormal", "heart_rate_gt_90", "rr_gt_20_or_paco2_lt_32", "wbc_abnormal", "suspected_infection", "organ_dysfunction", "fluid_resistant_hypotension", "multi_organ_failure"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "fractional_excretion_of_sodium",
                #             "description": "Calculates the fractional excretion of sodium (FENa) to assess renal function, • FENa <1%  → Suggests prerenal cause (e.g., hypovolemia) • FENa >2%  → Suggests intrinsic renal damage (e.g., acute tubular necrosis)",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "serum_creatinine": {
                #                         "type": "number",
                #                         "description": "Serum creatinine level in mg/dL"
                #                     },
                #                     "urine_sodium": {
                #                         "type": "number",
                #                         "description": "Urine sodium concentration in mEq/L"
                #                     },
                #                     "serum_sodium": {
                #                         "type": "number",
                #                         "description": "Serum sodium concentration in mEq/L"
                #                     },
                #                     "urine_creatinine": {
                #                         "type": "number",
                #                         "description": "Urine creatinine concentration in mg/dL"
                #                     },
                #                 },
                #                 "required": ["serum_creatinine", "urine_sodium", "serum_sodium", "urine_creatinine"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "free_water_deficit",
                #             "description": "Calculates the free water deficit (FWD) in liters based on serum sodium levels and body weight. • FWD = 0.6 × weight (kg) × (serum sodium - 140) / 140",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "weight_kg": {
                #                         "type": "number",
                #                         "description": "Patient’s weight in kilograms"
                #                     },
                #                     "current_sodium": {
                #                         "type": "number",
                #                         "description": "Patient’s current serum sodium in mEq/L"
                #                     },
                #                     "is_male": {
                #                         "type": "boolean",
                #                         "description": "True if patient is male"
                #                     },
                #                     "is_elderly": {
                #                         "type": "boolean",
                #                         "description": "True if patient is elderly (age > 65 years)"
                #                     },

                #                 },
                #                 "required": ["weight_kg", "current_sodium","is_male","is_elderly"]

                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             'name': 'gupta_perioperative_mica',
                #             'description': 'Calculates the Gupta Perioperative MICA score for predicting perioperative myocardial infarction and cardiac arrest risk.',
                #             'parameters': {
                #                 'type': 'object',
                #                 'properties': {
                #                     'age': {
                #                         'type': 'number',
                #                         'description': 'Age in years'
                #                     },
                #                     'functional_status': {
                #                         'type': 'string',
                #                         'description': 'One of: "independent", "partially_dependent", "totally_dependent".'
                #                     },
                #                     'asa_class': {
                #                         'type': 'string',
                #                         'description': 'ASA physical status class (1 to 5)'
                #                     },
                #                     'creatinine_status': {
                #                         'type': 'string',
                #                         'description': 'One of: "normal", "elevated", "unknown".'
                #                     },
                #                     'procedure_type': {
                #                         'type': 'string',
                #                         'description': 'One of predefined surgical procedure categories from the Gupta MICA model.'
                #                     },
                #                 },
                #                 'required': ['age', 'functional_status', 'asa_class', 'creatinine_status', 'procedure_type']
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "duke_activity_status_index",
                #             "description": "Calculates the Duke Activity Status Index (DASI) score for assessing functional capacity",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "self_care": {
                #                         "type": "boolean",
                #                         "description": "True if patient can take care of themselves"
                #                     },
                #                     "walk_indoors": {
                #                         "type": "boolean",
                #                         "description": "True if patient can walk indoors"
                #                     },
                #                     "walk_1_2_blocks": {
                #                         "type": "boolean",
                #                         "description": "True if patient can walk 1-2 blocks"
                #                     },
                #                     "climb_stairs": {
                #                         "type": "boolean",
                #                         "description": "True if patient can climb a flight of stairs"
                #                     },
                #                     "run_short_distance": {
                #                         "type": "boolean",
                #                         "description": "True if patient can run a short distance"
                #                     },
                #                     "light_work": {
                #                         "type": "boolean",
                #                         "description": "True if patient can do light work"
                #                     },
                #                     "moderate_work": {
                #                         "type": "boolean",
                #                         "description": "True if patient can do moderate work"
                #                     },
                #                     "heavy_work": {
                #                         "type": "boolean",
                #                         "description": "True if patient can do heavy work"
                #                     },
                #                     "yardwork": {
                #                         "type": "boolean",
                #                         "description": "True if patient can do yardwork"
                #                     },
                #                     "sexual_relations": {
                #                         "type": "boolean",
                #                         "description": "True if patient can have sexual relations"
                #                     },
                #                     "moderate_recreational": {
                #                         "type": "boolean",
                #                         "description": "True if patient can do moderate recreational activities"
                #                     },
                #                     "strenuous_sports": {
                #                         "type": "boolean",
                #                         "description": "True if patient can do strenuous sports"
                #                     }
                #                 },
                #                 "required": ["self_care", "walk_indoors", "walk_1_2_blocks", "climb_stairs", "run_short_distance", "light_work", "moderate_work", "heavy_work", "yardwork", "sexual_relations", "moderate_recreational", "strenuous_sports"]
                #             }
                #         }
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "ciwa_ar_score",
                #             "description": "Objectifies the severity of alcohol withdrawal based on symptoms",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "nausea_vomiting": {
                #                         "type": "number",
                #                         "description": "Nausea and vomiting score (0-7)"
                #                     },
                #                     "tremors": {
                #                         "type": "number",
                #                         "description": "Tremors score (0-7)"
                #                     },
                #                     "paroxysmal_sweats": {
                #                         "type": "number",
                #                         "description": "Paroxysmal sweats score (0-7)"
                #                     },
                #                     "anxiety": {
                #                         "type": "number",
                #                         "description": "Anxiety score (0-7)"
                #                     },
                #                     "agitation": {
                #                         "type": "number",
                #                         "description": "Agitation score (0-7)"
                #                     },
                #                     "tactile_disturbances": {
                #                         "type": "number",
                #                         "description": "Tactile disturbances score (0-7)"
                #                     },
                #                     "auditory_disturbances": {
                #                         "type": "number",
                #                         "description": "Auditory disturbances score (0-7)"
                #                     },
                #                     "visual_disturbances": {
                #                         "type": "number",
                #                         "description": "Visual disturbances score (0-7)"
                #                     },
                #                     "headache": {
                #                         "type": "number",
                #                         "description": "Headache score (0-7)"
                #                     },
                #                     "orientation": {
                #                         "type": "number",
                #                         "description": "Orientation score (0-4)"
                #                     },
                #                 },
                #                 "required": ["nausea_vomiting", "tremors", "paroxysmal_sweats", "anxiety", "agitation", "tactile_disturbances", "auditory_disturbances", "visual_disturbances", "headache", "orientation"],
                #             },
                #         },
                #     },
                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "psi_port_score",
                #             "description": "Estimates mortality risk for adult patients with community-acquired pneumonia (CAP) using the PSI/PORT scoring system.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "age": {
                #                         "type": "number",
                #                         "description": "Age in years"
                #                     },
                #                     "sex": {
                #                         "type": "string",
                #                         "description": "Sex of the patient ('Male' of 'Female)"
                #                     },
                #                     "nursing_home_resident": {
                #                         "type": "boolean",
                #                         "description": "Is the patient a nursing home resident?"
                #                     },
                #                     "neoplastic_disease": {
                #                         "type": "boolean",
                #                         "description": "History of neoplastic disease (cancer)"
                #                     },
                #                     "liver_disease": {
                #                         "type": "boolean",
                #                         "description": "History of liver disease"
                #                     },
                #                     "chf_history": {
                #                         "type": "boolean",
                #                         "description": "History of congestive heart failure"
                #                     },
                #                     "cerebrovascular_disease": {
                #                         "type": "boolean",
                #                         "description": "History of cerebrovascular disease"
                #                     },
                #                     "renal_disease": {
                #                         "type": "boolean",
                #                         "description": "History of renal disease"
                #                     },
                #                     "altered_mental_status": {
                #                         "type": "boolean",
                #                         "description": "Presence of altered mental status"
                #                     },
                #                     "resp_rate_30": {
                #                         "type": "boolean",
                #                         "description": "Respiratory rate ≥30 breaths/min"
                #                     },
                #                     "sbp_90": {
                #                         "type": "boolean",
                #                         "description": "Systolic blood pressure <90 mmHg"
                #                     },
                #                     "temp_35_39_9": {
                #                         "type": "boolean",
                #                         "description": "Temperature <35°C or >39.9°C"
                #                     },
                #                     "pulse_125": {
                #                         "type": "boolean",
                #                         "description": "Pulse ≥125 beats/min"
                #                     },
                #                     "ph_735": {
                #                         "type": "boolean",
                #                         "description": "pH <7.35"
                #                     },
                #                     "bun_30": {
                #                         "type": "boolean",
                #                         "description": "BUN ≥30 mg/dL or ≥11 mmol/L"
                #                     },
                #                     "sodium_130": {
                #                         "type": "boolean",
                #                         "description": "Sodium <130 mmol/L"
                #                     },
                #                     "glucose_250": {
                #                         "type": "boolean",
                #                         "description": "Glucose ≥250 mg/dL or ≥14 mmol/L"
                #                     },
                #                     "hematocrit_30": {
                #                         "type": "boolean",
                #                         "description": "Hematocrit <30%"
                #                     },
                #                     "pao2_60": {
                #                         "type": "boolean",
                #                         "description": "Partial pressure of oxygen <60 mmHg or <8 kPa"
                #                     },
                #                     "pleural_effusion": {
                #                         "type": "boolean",
                #                         "description": "Pleural effusion on chest x-ray"
                #                     }
                #                 },
                #                 "required": [
                #                     "age",
                #                     "sex",
                #                     "nursing_home_resident",
                #                     "neoplastic_disease",
                #                     "liver_disease",
                #                     "chf_history",
                #                     "cerebrovascular_disease",
                #                     "renal_disease",
                #                     "altered_mental_status",
                #                     "resp_rate_30",
                #                     "sbp_90",
                #                     "temp_35_39_9",
                #                     "pulse_125",
                #                     "ph_735",
                #                     "bun_30",
                #                     "sodium_130",
                #                     "glucose_250",
                #                     "hematocrit_30",
                #                     "pao2_60",
                #                     "pleural_effusion"
                #                 ]
                #             }
                #         }
                #     },

                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "serum_anion_gap",
                #             "description": "Calculates the Serum Anion Gap and related values, including corrections for albumin.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "sodium": {
                #                         "type": "number",
                #                         "description": "Sodium in mEq/L"
                #                     },
                #                     "chloride": {
                #                         "type": "number",
                #                         "description": "Chloride in mEq/L"
                #                     },
                #                     "bicarbonate": {
                #                         "type": "number",
                #                         "description": "Bicarbonate in mEq/L"
                #                     },
                #                     "albumin": {
                #                         "type": "number",
                #                         "description": "Albumin in g/dL"
                #                     }
                #                 },
                #                 "required": ["sodium", "chloride", "bicarbonate", "albumin"]
                #             }
                #         }
                #     },

                #     {
                #         "type": "function",
                #         "function": {
                #             "name": "serum_osmolarity",
                #             "description": "Calculates the serum osmolarity using sodium, BUN, glucose, and ethanol values.",
                #             "parameters": {
                #                 "type": "object",
                #                 "properties": {
                #                     "sodium": {
                #                         "type": "number",
                #                         "description": "Sodium concentration in mEq/L"
                #                     },
                #                     "bun": {
                #                         "type": "number",
                #                         "description": "Blood Urea Nitrogen (BUN) concentration in mg/dL"
                #                     },
                #                     "glucose": {
                #                         "type": "number",
                #                         "description": "Glucose concentration in mg/dL"
                #                     },
                #                     "ethanol": {
                #                         "type": "number",
                #                         "description": "Ethanol concentration in mg/dL"
                #                     }
                #                 },
                #                 "required": ["sodium", "bun", "glucose", "ethanol"]
                #             }
                #         }
                #     },

                # ]

                tools = []
                for name, obj in inspect.getmembers(mc, inspect.isfunction):
                    if obj.__module__ == mc.__name__:  # ensures it's defined in `mc`, not imported
                        schema = self.gen(obj)
                        tools.append(schema)


                # Initialize conversation with user's messages
                conversation = messages.copy()
                max_iterations = 10
                iterations = 0
                
                while iterations < max_iterations:
                    # Make API request
                    response = client.chat.completions.create(
                        model='gpt-4.1-mini',
                        messages=conversation,
                        tools=tools,
                        tool_choice="auto"
                    )
                    
                    message = response.choices[0].message
                    
                    # Important: Store the COMPLETE message object to preserve tool_calls
                    assistant_message = {
                        "role": "assistant",
                        "content": message.content or ""
                    }
                    
                    # If there are tool calls, add them to the message
                    if message.tool_calls:
                        assistant_message["tool_calls"] = [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                            for tool_call in message.tool_calls
                        ]
                    
                    # Add the complete assistant message to conversation
                    conversation.append(assistant_message)
                    
                    # If no tool calls, we're done
                    if not message.tool_calls:
                        ans = message.content
                        break
                        
                    # Process tool calls
                    tool_responses = []
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)
                        
                        if function_name == "egfr_epi":
                            result = self.to_dict(function_name,mc.egfr_epi(
                                scr=function_args["scr"], 
                                age=function_args["age"], 
                                male=function_args["male"]
                            ))
                        elif function_name == "crcl_cockcroft_gault":
                            result = self.to_dict(function_name,mc.crcl_cockcroft_gault(
                                age=function_args["age"],
                                weight=function_args["weight"],
                                height=function_args["height"],
                                scr=function_args["scr"],
                                sex=function_args["sex"]
                            ))
                        elif function_name == "egfr_epi_cr_cys":
                            result = self.to_dict(function_name,mc.egfr_epi_cr_cys(
                                scr=function_args["scr"],
                                scys=function_args["scys"],
                                age=function_args["age"],
                                male=function_args["male"]
                            ))                        
                        elif function_name == "mdrd_gfr":
                            result = self.to_dict(function_name,mc.mdrd_gfr(
                                scr=function_args["scr"],
                                age=function_args["age"],
                                is_black=function_args["is_black"],
                                is_female=function_args["is_female"]
                            ))
                        elif function_name == "bp_children":
                            result = self.to_dict(function_name,mc.bp_children(
                                years=function_args["years"],
                                months=function_args["months"],
                                height=function_args["height"],
                                sex=function_args["sex"],
                                systolic=function_args["systolic"],
                                diastolic=function_args["diastolic"]
                            ))
                        elif function_name == "bmi_calculator":
                            result = self.to_dict(function_name,mc.bmi_calculator(
                                weight=function_args["weight"],
                                height=function_args["height"],
                            ))
                        elif function_name == "bsa_calculator":
                            result = self.to_dict(function_name,mc.bsa_calculator(
                                weight=function_args["weight"],
                                height=function_args["height"],
                            ))

                        elif function_name == "map_calculator":
                            result = self.to_dict(function_name,mc.map_calculator(
                                sbp=function_args["sbp"],
                                dbp=function_args["dbp"]
                            ))
                        elif function_name == "chads2_vasc_score":
                            result = self.to_dict(function_name,mc.chads2_vasc_score(
                                age=function_args["age"],
                                female=function_args["female"],
                                chf=function_args["chf"],
                                hypertension=function_args["hypertension"],
                                stroke_history=function_args["stroke_history"],
                                vascular_disease=function_args["vascular_disease"],
                                diabetes=function_args["diabetes"]
                            ))
                        elif function_name == "prevent_cvd_risk":
                            result = self.to_dict(function_name,mc.prevent_cvd_risk(
                                age=function_args["age"],
                                female=function_args["female"],
                                tc=function_args["tc"],
                                hdl=function_args["hdl"],
                                sbp=function_args["sbp"],
                                diabetes=function_args["diabetes"],
                                current_smoker=function_args["current_smoker"],
                                egfr=function_args["egfr"],
                                using_antihtn=function_args["using_antihtn"],
                                using_statins=function_args["using_statins"],
                            ))
                        elif function_name == "corrected_calcium":
                            result = self.to_dict(function_name,mc.corrected_calcium(
                                serum_calcium=function_args["serum_calcium"],
                                patient_albumin=function_args["patient_albumin"],
                            ))
                        elif function_name == "qtc_calculator":
                            result = self.to_dict(function_name,mc.qtc_calculator(
                                qt_interval=function_args["qt_interval"],
                                heart_rate=function_args["heart_rate"],
                                formula=function_args.get("formula", "Bazett")  # default to Bazett if not specified
                            ))
                        elif function_name == "wells_pe_criteria":
                            result = self.to_dict(function_name,mc.wells_pe_criteria(
                                clinical_signs_dvt=function_args["clinical_signs_dvt"],
                                alternative_diagnosis_less_likely=function_args["alternative_diagnosis_less_likely"],
                                heart_rate_over_100=function_args["heart_rate_over_100"],
                                immobilization_or_surgery=function_args["immobilization_or_surgery"],
                                previous_dvt_or_pe=function_args["previous_dvt_or_pe"],
                                hemoptysis=function_args["hemoptysis"],
                                malignancy=function_args["malignancy"]
                            ))
                        elif function_name == "nihss_score":
                            result = self.to_dict(function_name,mc.nihss_score(
                                loc_alert=function_args["loc_alert"],
                                loc_respond=function_args["loc_respond"],
                                loc_commands=function_args["loc_commands"],
                                best_gaze=function_args["best_gaze"],
                                visual_field=function_args["visual_field"],
                                facial_palsy=function_args["facial_palsy"],
                                motor_arm_left=function_args["motor_arm_left"],
                                motor_arm_right=function_args["motor_arm_right"],
                                motor_leg_left=function_args["motor_leg_left"],
                                motor_leg_right=function_args["motor_leg_right"],
                                limb_ataxia=function_args["limb_ataxia"],
                                sensory=function_args["sensory"],
                                best_language=function_args["best_language"],
                                dysarthria=function_args["dysarthria"],
                                extinction_inattention=function_args["extinction_inattention"]
                            ))
                        elif function_name == "ibw_calculator":
                            result = self.to_dict(function_name,mc.ibw_calculator(
                                weight_kg=function_args["weight_kg"],
                                height_cm=function_args["height_cm"],
                                male=function_args["male"],
                            ))                        
                        elif function_name == "abw_calculator":
                            result = self.to_dict(function_name,mc.abw_calculator(
                                weight_kg=function_args["weight_kg"],
                                height_cm=function_args["height_cm"],
                                male=function_args["male"],
                            ))                        
                        elif function_name == "pregnancy_calculator":
                            result = self.to_dict(function_name,mc.pregnancy_calculator(
                                calculation_method=function_args["calculation_method"],
                                date_value=function_args["date_value"],
                                cycle_length=function_args.get("cycle_length"),
                                gestational_age_weeks=function_args.get("gestational_age_weeks"),
                                gestational_age_days=function_args.get("gestational_age_days")
                            ))

                        elif function_name == "revised_cardiac_risk_index":
                            result = self.to_dict(function_name,mc.revised_cardiac_risk_index(
                                high_risk_surgery=function_args["high_risk_surgery"],
                                ischemic_heart_disease=function_args["ischemic_heart_disease"],
                                congestive_heart_failure=function_args["congestive_heart_failure"],
                                cerebrovascular_disease=function_args["cerebrovascular_disease"],
                                insulin_treatment=function_args["insulin_treatment"],
                                creatinine_over_2mg=function_args["creatinine_over_2mg"]
                            ))

                        elif function_name == "child_pugh_score":
                            result = self.to_dict(function_name,mc.child_pugh_score(
                                bilirubin=function_args["bilirubin"],
                                albumin=function_args["albumin"],
                                ascites=function_args["ascites"],
                                inr=function_args["inr"],
                                encephalopathy_grade=function_args["encephalopathy_grade"]
                            ))
                        elif function_name == "phq9_score":
                            result = self.to_dict(function_name,mc.phq9_score(
                                interest=function_args["interest"],
                                depressed=function_args["depressed"],
                                sleep=function_args["sleep"],
                                tired=function_args["tired"],
                                appetite=function_args["appetite"],
                                feeling_bad=function_args["feeling_bad"],
                                concentration=function_args["concentration"],
                                movement=function_args["movement"],
                                self_harm=function_args["self_harm"]
                            ))
                        elif function_name == "heart_score":
                            result = self.to_dict(function_name,mc.heart_score(
                                history=function_args["history"],
                                ekg=function_args["ekg"],
                                age=function_args["age"],
                                risk_factors=function_args["risk_factors"],
                                troponin=function_args["troponin"]
                            ))
                        elif function_name == "stop_bang_score":
                            result = self.to_dict(function_name,mc.stop_bang_score(
                                snoring=function_args["snoring"],
                                tired=function_args["tired"],
                                observed_apnea=function_args["observed_apnea"],
                                bp_high=function_args["bp_high"],
                                bmi_over_35=function_args["bmi_over_35"],
                                age_over_50=function_args["age_over_50"],
                                neck_over_40cm=function_args["neck_over_40cm"],
                                male=function_args["male"],
                            ))
                        elif function_name == "has_bled_score":
                            result = self.to_dict(function_name,mc.has_bled_score(
                                hypertension=function_args["hypertension"],
                                abnormal_renal_function=function_args["abnormal_renal_function"],
                                abnormal_liver_function=function_args["abnormal_liver_function"],
                                stroke_history=function_args["stroke_history"],
                                bleeding_history=function_args["bleeding_history"],
                                labile_inr=function_args["labile_inr"],
                                elderly=function_args["elderly"],
                                drugs=function_args["drugs"],
                                alcohol=function_args["alcohol"],
                            ))
                        elif function_name == "centor_score_modified":
                            result = self.to_dict(function_name,mc.centor_score_modified(
                                age=function_args["age"],
                                tonsillar_exudate=function_args["tonsillar_exudate"],
                                swollen_lymph_nodes=function_args["swollen_lymph_nodes"],
                                fever=function_args["fever"],
                                cough_absent=function_args["cough_absent"]
                            ))
                        elif function_name == "glasgow_coma_scale":
                            result = self.to_dict(function_name,mc.glasgow_coma_scale(
                                eye_response=function_args["eye_response"],
                                verbal_response=function_args["verbal_response"],
                                motor_response=function_args["motor_response"]
                            ))
                        elif function_name == "caprini_score":
                            result = self.to_dict(function_name,mc.caprini_score(
                                age=function_args["age"],
                                sex=function_args["sex"],
                                surgery_type=function_args["surgery_type"],
                                recent_major_surgery=function_args["recent_major_surgery"],
                                chf=function_args["chf"],
                                sepsis=function_args["sepsis"],
                                pneumonia=function_args["pneumonia"],
                                immobilizing_cast=function_args["immobilizing_cast"],
                                fracture=function_args["fracture"],
                                stroke=function_args["stroke"],
                                multiple_trauma=function_args["multiple_trauma"],
                                spinal_cord_injury=function_args["spinal_cord_injury"],
                                varicose_veins=function_args["varicose_veins"],
                                swollen_legs=function_args["swollen_legs"],
                                central_venous_access=function_args["central_venous_access"],
                                history_dvt_pe=function_args["history_dvt_pe"],
                                family_history_thrombosis=function_args["family_history_thrombosis"],
                                factor_v_leiden=function_args["factor_v_leiden"],
                                prothrombin_20210a=function_args["prothrombin_20210a"],
                                homocysteine=function_args["homocysteine"],
                                lupus_anticoagulant=function_args["lupus_anticoagulant"],
                                anticardiolipin_antibody=function_args["anticardiolipin_antibody"],
                                hit=function_args["hit"],
                                other_thrombophilia=function_args["other_thrombophilia"],
                                mobility_status=function_args["mobility_status"],
                                ibd=function_args["ibd"],
                                bmi_over_25=function_args["bmi_over_25"],
                                acute_mi=function_args["acute_mi"],
                                copd=function_args["copd"],
                                malignancy=function_args["malignancy"],
                                other_risk_factors=function_args["other_risk_factors"]
                            ))
                        elif function_name == "ldl_calculated":
                            result = self.to_dict(function_name,mc.ldl_calculated(
                                total_cholesterol=function_args["total_cholesterol"],
                                hdl=function_args["hdl"],
                                triglycerides=function_args["triglycerides"]
                            ))
                        elif function_name == "sofa_score":
                            result = self.to_dict(function_name,mc.sofa_score(
                                pao2_fio2=function_args["pao2_fio2"],
                                mechanically_ventilated=function_args["mechanically_ventilated"],
                                platelets=function_args["platelets"],
                                gcs=function_args["gcs"],
                                bilirubin=function_args["bilirubin"],
                                map_mmHg=function_args["map_mmHg"],
                                dopamine=function_args["dopamine"],
                                dobutamine=function_args["dobutamine"],
                                epinephrine=function_args["epinephrine"],
                                norepinephrine=function_args["norepinephrine"],
                                creatinine=function_args["creatinine"],
                                urine_output_ml_per_day=function_args["urine_output_ml_per_day"]
                            ))
                        elif function_name == "perc_rule":
                            result = self.to_dict(function_name,mc.perc_rule(
                                age_over_50=function_args["age_over_50"],
                                heart_rate_100_or_more=function_args["heart_rate_100_or_more"],
                                oxygen_sat_below_95=function_args["oxygen_sat_below_95"],
                                unilateral_leg_swelling=function_args["unilateral_leg_swelling"],
                                hemoptysis=function_args["hemoptysis"],
                                recent_trauma_or_surgery=function_args["recent_trauma_or_surgery"],
                                prior_pe_or_dvt=function_args["prior_pe_or_dvt"],
                                hormone_use=function_args["hormone_use"]
                            ))
                        elif function_name == "gad7_score":
                            result = self.to_dict(function_name,mc.gad7_score(
                                q1=function_args["q1"],
                                q2=function_args["q2"],
                                q3=function_args["q3"],
                                q4=function_args["q4"],
                                q5=function_args["q5"],
                                q6=function_args["q6"],
                                q7=function_args["q7"]
                            ))
                        elif function_name == "curb65_score":
                            result = self.to_dict(function_name,mc.curb65_score(
                                confusion=function_args["confusion"],
                                bun_over_19=function_args["bun_over_19"],
                                respiratory_rate_30_or_more=function_args["respiratory_rate_30_or_more"],
                                low_blood_pressure=function_args["low_blood_pressure"],
                                age_65_or_more=function_args["age_65_or_more"]
                            ))                        

                        elif function_name == "steroid_conversion":
                            result = self.to_dict(function_name,mc.steroid_conversion(
                                from_steroid=function_args["from_steroid"],
                                from_dose_mg=function_args["from_dose_mg"],
                                to_steroid=function_args["to_steroid"]
                            ))                        
                        elif function_name == "calculate_mme":
                            result = self.to_dict(function_name,mc.calculate_mme(
                                opioid=function_args["opioid"],
                                dose_per_administration=function_args["dose_per_administration"],
                                doses_per_day=function_args["doses_per_day"]
                            ))
                        elif function_name == "maintenance_fluids":
                            result = self.to_dict(function_name,mc.maintenance_fluids(
                                weight_kg=function_args["weight_kg"]
                            ))
                        elif function_name == "correctedsodiumkatz":
                            result = self.to_dict(function_name,mc.corrected_sodium_katz(
                                measured_sodium=function_args["measured_sodium"],
                                serum_glucose=function_args["serum_glucose"]
                            ))
                        elif function_name == "correctedsodiumhillier":
                            result = self.to_dict(function_name,mc.corrected_sodium_hillier(
                                measured_sodium=function_args["measured_sodium"],
                                serum_glucose=function_args["serum_glucose"]
                            ))
                        elif function_name == "meld_3":
                            result = self.to_dict(function_name,mc.meld_3(
                                age=function_args["age"],
                                female=function_args["female"],
                                bilirubin=function_args["bilirubin"],
                                inr=function_args["inr"],
                                creatinine=function_args["creatinine"],
                                albumin=function_args["albumin"],
                                sodium=function_args["sodium"],
                                dialysis=function_args["dialysis"]
                            ))
                        elif function_name == "framingham_risk_score":
                            result = self.to_dict(function_name,mc.framingham_risk_score(
                                age=function_args["age"],
                                total_cholesterol=function_args["total_cholesterol"],
                                hdl_cholesterol=function_args["hdl_cholesterol"],
                                systolic_bp=function_args["systolic_bp"],
                                treated_for_bp=function_args["treated_for_bp"],
                                smoker=function_args["smoker"],
                                gender=function_args["gender"],
                            ))
                        elif function_name == "homa_ir":
                            result = self.to_dict(function_name,mc.homa_ir(
                                fasting_insulin=function_args["fasting_insulin"],
                                fasting_glucose=function_args["fasting_glucose"]
                            ))
                        
                        elif function_name == "fib4_index":
                            result = self.to_dict(function_name,mc.fib4_index(
                                age=function_args["age"],
                                ast=function_args["ast"],
                                alt=function_args["alt"],
                                platelets=function_args["platelets"]
                            ))
                        elif function_name == "ariscat_score":
                            result = self.to_dict(function_name,mc.ariscat_score(
                                age=function_args["age"],
                                spo2=function_args["spo2"],
                                recent_respiratory_infection=function_args["recent_respiratory_infection"],
                                preop_anemia=function_args["preop_anemia"],
                                surgical_site=function_args["surgical_site"],
                                surgery_duration_hrs=function_args["surgery_duration_hrs"],
                                emergency_surgery=function_args["emergency_surgery"]
                            ))
                        elif function_name == "sepsis_criteria":
                            result = self.to_dict(function_name,mc.sepsis_criteria(
                                temp_abnormal=function_args["temp_abnormal"],
                                heart_rate_gt_90=function_args["heart_rate_gt_90"],
                                rr_gt_20_or_paco2_lt_32=function_args["rr_gt_20_or_paco2_lt_32"],
                                wbc_abnormal=function_args["wbc_abnormal"],
                                suspected_infection=function_args["suspected_infection"],
                                organ_dysfunction=function_args["organ_dysfunction"],
                                fluid_resistant_hypotension=function_args["fluid_resistant_hypotension"],
                                multi_organ_failure=function_args["multi_organ_failure"]
                            ))
                        elif function_name == "fractional_excretion_of_sodium":
                            result = self.to_dict(function_name,mc.fractional_excretion_of_sodium(
                                serum_creatinine=function_args["serum_creatinine"],
                                urine_sodium=function_args["urine_sodium"],
                                serum_sodium=function_args["serum_sodium"],
                                urine_creatinine=function_args["urine_creatinine"]
                            ))
                        elif function_name == "free_water_deficit":
                            result = self.to_dict(function_name, mc.free_water_deficit(
                                weight_kg=function_args["weight_kg"],
                                current_sodium=function_args["current_sodium"],
                                is_male=function_args["is_male"],
                                is_elderly=function_args["is_elderly"]
                            ))
                        
                        elif function_name == "gupta_perioperative_mica":
                            result = self.to_dict(function_name, mc.gupta_perioperative_mica(
                                age=function_args["age"],
                                functional_status=function_args["functional_status"],
                                asa_class=function_args["asa_class"],
                                creatinine_status=function_args["creatinine_status"],
                                procedure_type=function_args["procedure_type"]
                            ))

                        elif function_name == "duke_activity_status_index":
                            result = self.to_dict(function_name, mc.duke_activity_status_index(
                                self_care=function_args["self_care"],
                                walk_indoors=function_args["walk_indoors"],
                                walk_1_2_blocks=function_args["walk_1_2_blocks"],
                                climb_stairs=function_args["climb_stairs"],
                                run_short_distance=function_args["run_short_distance"],
                                light_work=function_args["light_work"],
                                moderate_work=function_args["moderate_work"],
                                heavy_work=function_args["heavy_work"],
                                yardwork=function_args["yardwork"],
                                sexual_relations=function_args["sexual_relations"],
                                moderate_recreational=function_args["moderate_recreational"],
                                strenuous_sports=function_args["strenuous_sports"]
                            ))

                        elif function_name == "ciwa_ar_score":
                            result = self.to_dict(function_name, mc.ciwa_ar_score(
                                nausea_vomiting=function_args["nausea_vomiting"],
                                tremors=function_args["tremors"],
                                paroxysmal_sweats=function_args["paroxysmal_sweats"],
                                anxiety=function_args["anxiety"],
                                agitation=function_args["agitation"],
                                tactile_disturbances=function_args["tactile_disturbances"],
                                auditory_disturbances=function_args["auditory_disturbances"],
                                visual_disturbances=function_args["visual_disturbances"],
                                headache=function_args["headache"],
                                orientation=function_args["orientation"]
                            ))
                        elif function_name == "psi_port_score":
                            result = self.to_dict(function_name, mc.psi_port_score(
                                age=function_args["age"],
                                sex=function_args["sex"],
                                nursing_home_resident=function_args["nursing_home_resident"],
                                neoplastic_disease=function_args["neoplastic_disease"],
                                liver_disease=function_args["liver_disease"],
                                chf_history=function_args["chf_history"],
                                cerebrovascular_disease=function_args["cerebrovascular_disease"],
                                renal_disease=function_args["renal_disease"],
                                altered_mental_status=function_args["altered_mental_status"],
                                resp_rate_30=function_args["resp_rate_30"],
                                sbp_90=function_args["sbp_90"],
                                temp_35_39_9=function_args["temp_35_39_9"],
                                pulse_125=function_args["pulse_125"],
                                ph_735=function_args["ph_735"],
                                bun_30=function_args["bun_30"],
                                sodium_130=function_args["sodium_130"],
                                glucose_250=function_args["glucose_250"],
                                hematocrit_30=function_args["hematocrit_30"],
                                pao2_60=function_args["pao2_60"],
                                pleural_effusion=function_args["pleural_effusion"]
                            ))
                        elif function_name == "serum_anion_gap":
                            result = self.to_dict(function_name, mc.serum_anion_gap(
                                sodium=function_args["sodium"],
                                chloride=function_args["chloride"],
                                bicarbonate=function_args["bicarbonate"],
                                albumin=function_args["albumin"]
                            ))
                        elif function_name == "serum_osmolarity":
                            result = self.to_dict(function_name, mc.serum_osmolarity(
                                sodium=function_args["sodium"],
                                bun=function_args["bun"],
                                glucose=function_args["glucose"],
                                ethanol=function_args["ethanol"]
                            ))

                        else:
                            result = f"Error: Function {function_name} not implemented"
                            
                        # Create proper tool response
                        tool_responses.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": str(result)
                        })
                    
                    # Add all tool responses to conversation
                    conversation.extend(tool_responses)
                    
                    iterations += 1
                
                # If we hit max iterations, use the last response
                if iterations == max_iterations:
                    last_assistant_messages = [msg for msg in reversed(conversation) if msg.get("role") == "assistant"]
                    ans = last_assistant_messages[0]["content"] if last_assistant_messages else "Max iterations reached without resolution"

            else:
                stopping_criteria = None
                if prompt is None:
                    prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                if "meditron" in self.llm_name.lower():
                    stopping_criteria = self.custom_stop(["###", "User:", "\n\n\n"], input_len=len(self.tokenizer.encode(prompt, add_special_tokens=True)))
                if "llama-3" in self.llm_name.lower():
                    response = self.model(
                        prompt,
                        do_sample=False,
                        eos_token_id=[self.tokenizer.eos_token_id, self.tokenizer.convert_tokens_to_ids("<|eot_id|>")],
                        pad_token_id=self.tokenizer.eos_token_id,
                        max_length=min(self.max_length, len(self.tokenizer.encode(prompt, add_special_tokens=True)) + 4096),
                        truncation=True,
                        stopping_criteria=stopping_criteria,
                        temperature=0.0
                    )
                else:
                    response = self.model(
                        prompt,
                        do_sample=False,
                        eos_token_id=self.tokenizer.eos_token_id,
                        pad_token_id=self.tokenizer.eos_token_id,
                        max_length=min(self.max_length, len(self.tokenizer.encode(prompt, add_special_tokens=True)) + 4096),
                        truncation=True,
                        stopping_criteria=stopping_criteria,
                        temperature=0.0
                    )
                ans = response[0]["generated_text"]


        else:
            if "openai" in self.llm_name.lower():
                client = openai.OpenAI()

                response = client.chat.completions.create(
                        model=self.model,
                        messages=messages
                )

                ans = response.choices[0].message.content

            else:
                stopping_criteria = None
                if prompt is None:
                    prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                if "meditron" in self.llm_name.lower():
                    stopping_criteria = self.custom_stop(["###", "User:", "\n\n\n"], input_len=len(self.tokenizer.encode(prompt, add_special_tokens=True)))
                if "llama-3" in self.llm_name.lower():
                    response = self.model(
                        prompt,
                        do_sample=False,
                        eos_token_id=[self.tokenizer.eos_token_id, self.tokenizer.convert_tokens_to_ids("<|eot_id|>")],
                        pad_token_id=self.tokenizer.eos_token_id,
                        max_length=min(self.max_length, len(self.tokenizer.encode(prompt, add_special_tokens=True)) + 4096),
                        truncation=True,
                        stopping_criteria=stopping_criteria,
                        temperature=0.0
                    )
                else:
                    response = self.model(
                        prompt,
                        do_sample=False,
                        eos_token_id=self.tokenizer.eos_token_id,
                        pad_token_id=self.tokenizer.eos_token_id,
                        max_length=min(self.max_length, len(self.tokenizer.encode(prompt, add_special_tokens=True)) + 4096),
                        truncation=True,
                        stopping_criteria=stopping_criteria,
                        temperature=0.0
                    )
                ans = response[0]["generated_text"]
        return ans


class CustomStoppingCriteria(StoppingCriteria):
    def __init__(self, stop_words, tokenizer, input_len=0):
        super().__init__()
        self.tokenizer = tokenizer
        self.stops_words = stop_words
        self.input_len = input_len

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        tokens = self.tokenizer.decode(input_ids[0][self.input_len:])
        return any(stop in tokens for stop in self.stops_words)    