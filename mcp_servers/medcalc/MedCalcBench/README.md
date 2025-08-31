# MedCalc-Bench

<br>

<div style="text-align: center;">
  <img alt="MedCalc-Bench" src="https://github.com/ncbi-nlp/MedCalc-Bench/blob/main/instance_illustration/instance_illustration.png">
</div>

<br>

MedCalc-Bench is the first medical calculation dataset used to benchmark LLMs ability to serve as clinical calculators. Each instance in the dataset consists of a patient note, a question asking to compute a specific clinical value, a final answer value, and a step-by-step solution explaining how the final answer was obtained. Our dataset covers 55 different calculation tasks which are either rule-based calculations or are equation-based calculations. This dataset contains a training dataset of 10,053 instances and a testing dataset of 1,047 instances.
 <br>

In all, we hope that our dataset and benchmark serves as a call to improve the computational reasoning skills of LLMs in medical settings. 

Our preprint is available at: https://arxiv.org/abs/2406.12036.

## MedCalc-Bench Dataset

To download the CSV for the MedCalc-Bench evaluation dataset, please download the file, `test_data.csv` inside the `dataset` folder of this repository. You can also download the test set split from HuggingFace at [https://huggingface.co/datasets/ncbi/MedCalc-Bench](https://huggingface.co/datasets/ncbi/MedCalc-Bench-v1.0). 

In addition to the 1,047 evaluation instances, we also provide a training dataset of 10,053 instances which can be used for fine-tuning open-source LLMs (see Section C of the Appendix). The training data can be found in the ```dataset/train_data.csv.zip``` file and can be unzipped to obtain ```train_data.csv```. This training dataset can also be found in the train split of the HuggingFace link. 

Each Instance in the dataset contains the following information: 

- **Row Number**: Specifies the index of the instance.
- **Calculator ID**: Specifies the integer ID of the calculator.
- **Calculator Name**: Specifies the name of the clinical calculation task.
- **Category**: Specifies the sub-category of the calculator. For equation-based calculators, the options are lab test, dosage, date, or physical and for rule-based calculators, the options are risk, severity, and diagnosis.
- **Output Type**: Specifies the format type that the calculator will return. The options are decimal, integer, date (MM/DD/YY), or time in terms of weeks and days (i.e. (17 weeks, 4 days)).
- **Note ID**: Specifies the ID of the patient note. The ID of the note will either be the ID given by Open-Patients or it will be an integer value if the patient note was handwritten by clinicians or synthesized by a template.
- **Note Type**: Specifies whether the patient note was synthesized by a clinician (Handwritten), produced from a template (Template), or was extracted from PMC-Patients (extracted).
- **Patient Note**: Specifies the patient note which provides the information needed to compute the final answer.
- **Question**: Specifies the question that is asked to the model to compute a specific medical value based on a particular calculator.
- **Relevant Entities**: Provides a dictionary of the parameters and their extracted values based on the patient note.
- **Ground Truth Answer**: Specifies the ground truth value without any units for the medical value that needs to be calculated.
- **Lower Limit**: For equation-based calculators whose output is a decimal, this value is 95% of the ground truth answer value. For all other cases, the lower limit is the same as the ground-truth value.
- **Upper Limit**: For equation-based calculators whose output is a decimal, this value is 105% of the ground truth answer value. For all other cases, the upper limit is the same as the ground-truth value.
- **Ground Truth Explanation**: The ground truth explanation for the data instance providing a step-by-step explanation for how the final answer was obtained.

## Reproducing Main Results 

To install all the packages needed for this project, please run the following command: ```conda env create -f environment.yml```. Alternatively, you can install the environment via `pip` using ```pip install -r requirements.txt```. This command will create the ```medcalc-bench``` conda environment. For running OpenAI models, you will need to provide your OpenAI key in this conda environment. You can do this by executing the following command in the ```medcalc-bench``` environment: ```export OPENAI_API_KEY = YOUR_API_KEY```, where YOUR_API_KEY is your OpenAI API key. You will also need to provide your HuggingFace token in this environment by running the following command: ```export HUGGINGFACE_TOKEN=your_hugging_face_token```, where ```your_hugging_face_token``` is your huggingface token. 


For reproducing the Table 2 from the paper, first `cd` into the `evaluation` folder. Then, please run the following command: ```python run.py --model <model_name> and --prompt <prompt_style>```.

The options for `--model` are below:

- Mistral-7B: mistralai/Mistral-7B-Instruct-v0.2
- Mixtral-8x7B: mistralai/Mixtral-8x7B-Instruct-v0.1
- Llama3-8B: meta-llama/Meta-Llama-3-8B-Instruct
- Llama3-70B: meta-llama/Meta-Llama-3-70B-Instruct
- Meditron-70B: epfl-llm/meditron-70b
- GPT-3.5: OpenAI/gpt-3.5-turbo
- GPT-4: OpenAI/gpt-4
- PMC-Llama-13B: axiong/PMC_LLaMA_13B

The options for `--prompt` are below:

- Direct Answer: direct_answer 
- Zero Shot Chain of Thought: zero_shot
- One Shot Chain of Though: one_shot_cot

From this, you will get one jsonl file outputting the status of every question: Upon executing `run.py`, the results will be saved in a file called ```<model>_<prompt>.jsonl```. This file can be found in the ```outputs``` folder. 

Each instance in the jsonl will have the following meta-data associated with them:

<br>

```
{
  "Row Number": Row index of the item,
  "Calculator Name": Name of calculation task,
  "Calculator ID": ID of the calculator,
  "Category": type of calculation (risk, severity, diagnosis for rule-based calculators and lab, risk, physical, date, dosage for equation-based calculators),
  "Note ID": ID of the note taken directly from MedCalc-Bench,
  "Patient Note": Paragraph which is the patient note taken directly from MedCalc-Bench,
  "Question": Question asking for a specific medical value to be computed,
  "LLM Answer": Final Answer Value from LLM, 
  "LLM Explanation": Step-by-Step explanation by LLM,
  "Ground Truth Answer": Ground truth answer value,
  "Ground Truth Explanation": Step-by-step ground truth explanation,
  "Result": "Correct" or "Incorrect"
}
```

Additionally, we provide the mean accuracy and standard deviation percentage for each sub-category in a json titled ```results_<model>_<prompt_style>.json```. The cumulative accuracy and standard deviation among all 1,047 instances can be found under "overall" key of the JSON. This file can be found in the ```results``` folder. 

## Reproducing Code Interpreter Results

In addition to the results for Table 2 in the main paper, we also prompted LLMs to write code to perform arithmetic instead of having the LLM do this itself. The results for this can be found in Appendix D. Due to limited compute, we only ran the results for GPT-3.5 and GPT-4. To examine the prompts and run under this setting, please examine the ```generate_code_prompt.py``` file in the ```evaluation``` folder. 

To run this code, simply `cd` into the ```evaluations``` folder and run the following: ```python generate_code_prompt.py --gpt <gpt_model>```. The options for ```<gpt_model>``` are either `4` for running GPT-4 or `35` to run GPT-3.5-turbo-16k. The results will then get saved in a jsonl file named: ```code_exec_{model_name}.jsonl``` in the  ```outputs``` folder. Note that in this case, ```model_name``` will be ```gpt_4``` if you chose to run using GPT-4. Otherwise, ```model_name``` will be ```gpt_35_16k``` if you selected to run with GPT-3.5-turbo. 

The metadata for each instance in the jsonl file for the code interprepter results is the same instance info provided in the section above. The only difference is that we store the LLM chat history between the user and the assistant and have a "LLM Chat History" key instead of the "LLM Explanation" key. Additionally, the sub-category and overall accuracy are stored in a JSON file named 
```results_<model_name>_code_augmented.json```. This JSON is located in the ```results``` folder. 

## Acknowledgments and Disclosure of Funding

This research was supported by the NIH Intramural Research Program, National Library of Medicine. Additionally, the contributions made by Soren Dunn were done using the Delta advanced computing and data resource which is supported by the National Science Foundation (award OAC tel:2005572) and the State of Illinois. Delta is a joint effort of the University of Illinois Urbana-Champaign (UIUC) and its National Center for Supercomputing Applications (NCSA).

## Ethics Statement

For curating the patient notes in MedCalc-Bench, we only use publicly available patient notes from published case report articles in PubMed Central and clinician-generated anonymous patient vignettes. As such, no identifiable personal health information is revealed in this study. While MedCalc-Bench is designed to evaluate the medical calculation capabilities of LLMs, it should be noted that the dataset is not intended for direct diagnostic use or medical decision-making without review and oversight by a clinical professional. Individuals should not change their health behavior solely on the basis of our study.


## Broader Impacts 

As described in Sec 1, medical calculators are commonly used in the clinical setting. With the rapidly growing interest in using LLMs for domain-specific applications, healthcare practitioners might directly prompt chatbots like ChatGPT to perform medical calculation tasks. However, the capabilities of LLMs in these tasks are currently unknown. Since healthcare is a high-stakes domain and wrong medical calculations can lead to severe consequences, including misdiagnosis, inappropriate treatment plans, and potential harm to patients, it is crucial to thoroughly evaluate the performance of LLMs in
medical calculations. Surprisingly, the evaluation results on our MedCalc-Bench dataset show that all the studied LLMs struggle in the medical calculation tasks. The most capable model GPT-4 achieves only 50% accuracy with one-shot learning and chain-of-thought prompting. As such, our study indicates that current LLMs are not yet ready to be used for medical calculations. It should be noted that while high scores on MedCalc-Bench do not guarantee excellence in medical calculation tasks, failing in this dataset indicates that the models must not be considered for such purposes at all. In other words, we believe that passing MedCalc-Bench should be a necessary (but not sufficient) condition for a model to be used for medical calculation

## Maintenance and Responsibility 

For any changes to this dataset, (i.e. adding new notes or calculators), we will update the README instructions, test_set.csv, and train_set.csv. We will still keep older versions of these datasets in an `archive/` folder. We will also update train and test sets for HuggingFace as well. 

## Disclaimer

This tool shows the results of research conducted in the Computational Biology Branch, NCBI/NLM. The information produced on this website is not intended for direct diagnostic use or medical decision-making without review and oversight by a clinical professional. Individuals should not change their health behavior solely on the basis of information produced on this website. NIH does not independently verify the validity or utility of the information produced by this tool. If you have questions about the information produced on this website, please see a health care professional. More information about NCBI's disclaimer policy is available.

## Citation

```bibtex
@misc{khandekar2024medcalcbench,
      title={MedCalc-Bench: Evaluating Large Language Models for Medical Calculations}, 
      author={Nikhil Khandekar and Qiao Jin and Guangzhi Xiong and Soren Dunn and Serina S Applebaum and Zain Anwar and Maame Sarfo-Gyamfi and Conrad W Safranek and Abid A Anwar and Andrew Zhang and Aidan Gilson and Maxwell B Singer and Amisha Dave and Andrew Taylor and Aidong Zhang and Qingyu Chen and Zhiyong Lu},
      year={2024},
      eprint={2406.12036},
      archivePrefix={arXiv},
      primaryClass={id='cs.CL' full_name='Computation and Language' is_active=True alt_name='cmp-lg' in_archive='cs' is_general=False description='Covers natural language processing. Roughly includes material in ACM Subject Class I.2.7. Note that work on artificial languages (programming languages, logics, formal systems) that does not explicitly address natural-language issues broadly construed (natural-language processing, computational linguistics, speech, text retrieval, etc.) is not appropriate for this area.'}
}
```
