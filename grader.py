# Testing tool for automatic analysis of group assignments
# Remember to set keys/endpoints for the service you wish to use.
#
# instructions:
# python3 -m venv venv
# source venv/bin/activate
# pip install PyPDF2
# pip install openai
# pip install pandas
# python3 grader.py
#
#
# Known problems:
# - The prompts+instructions never seem to figure out if references are included in any of the documents
# - Repeted runs of the same pdf produce slightly varying results
# - Always check the total points from the (calculated) printout, sometimes the GPT decides to print a sum of the points itself, this is not to be trusted (GPTs don't know math)
#
from PyPDF2 import PdfReader
from openai import AzureOpenAI
from openai import OpenAI
import difflib
import time
import pandas as pd

PDF_DIRECTORY = "./data/" # pdf data directory
GRADING_DIRECTORY = "./grading/"  # where the final grades will be saved
GRADING_SUFFIX = ".grades.md"
POINTS_FILE = "points_template.csv"
ASSIGNMENT_SPECIFICATION = "assignment.pdf"
GRADING_INSTRUCTIONS = "instructions.md" # the grading instructions
AZURE_MODEL_ENGINE = "gpt-4o-mini"
AZURE_API_KEY="YOUR AZURE API KEY"
AZURE_API_VERSION="2024-07-01-preview"
AZURE_ENDPOINT = "YOUR AZURE END POINT"
OPENAI_API_KEY = "YOUR OPENAI KEY"
OPENAI_MODEL_ENGINE = "gpt-4o-mini"
AI_TEMPERATURE = 0.0
LLAMA_API_KEY = "token-not-needed-right-now",
LLAMA_BASE_URL = "YOUR LLAMA BASE URL PATH"
LLAMA_MODEL = "tgi"
RETRY_WAIT_DURATION = 70 # in seconds
MAX_RETRIES = 3
CLIENT_TYPE = 0 # 0 = azure, 1 = openai, 2 = ollama

def read_data_file(file_path):
    return pd.read_csv(file_path)

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n\n"
    return text

def create_system_prompts():
    prompts = ["You are a teacher in a software design course. Your task is to grade group assignment exercise submissions. The assignment's goal was to create a test plan document. This test plan, also referred as the document, is given as a user input. Carefully go through each work. In case of unclear or ambiguous content, assume that content is missing. Do NOT make up content. ONLY look at the user's (student's) work."]
    #prompts.append(f"Here are the assignment instructions given to the students: {extract_text_from_pdf(ASSIGNMENT_SPECIFICATION)}")
    with open(GRADING_INSTRUCTIONS, 'r') as file:
        prompts.append(f"Copy each line from the instructions exactly as listed, including the point values. Do NOT modify the grading instruction lines when generating output. Here are the grading instructions: {file.read()}")
    return prompts

def call_openai(client, system_prompts, user_prompt):
    print("Calling openai...")
    return call_openai_api(client, system_prompts, user_prompt, OPENAI_MODEL_ENGINE)

def call_azure(client, system_prompts, user_prompt):
    print("Calling azure...")
    return call_openai_api(client, system_prompts, user_prompt, AZURE_MODEL_ENGINE)

def call_openai_api(client, system_prompts, user_prompt, model_engine):
    messages = []
    for s in system_prompts:
        messages.append({"role": "system", "content": s}) #o1 models do not support system role, replace "system" with "user"
    messages.append({"role": "user", "content": user_prompt})
    response = None
    try:
        #response = client.chat.completions.create(model=model_engine, messages=messages)  # o1 models do not support temperature, remove parameter
        response = client.chat.completions.create(model=model_engine, messages=messages, temperature=AI_TEMPERATURE) 
    except Exception as e:
        print(f"Exception during generation: {e}\n\n Trying again...")
        response = None
    return response

def call_llama(client, system_prompts, user_prompt):
    print("Calling llama...")
    messages = []
    for s in system_prompts:
        messages.append({"role": "system", "content": s})
    messages.append({"role": "user", "content": user_prompt})

    response=client.chat.completions.create(model=LLAMA_MODEL, messages=messages, temperature=AI_TEMPERATURE, max_tokens=1000) 
    return response

def run_tests(client, data):
    system_prompts = create_system_prompts()
    print(f"Using system prompts:\n{system_prompts}")

    print("Starting to process...")
    start_time = time.time()

    for index, row in data.iterrows():
        pdf = row['pdf']
        if pdf and isinstance(pdf, str): # ignore rows without pdf
            pdf_path = PDF_DIRECTORY+pdf
            extract_start_time = time.time()
            print(f"Extracting from pdf: {pdf_path}")
            text = extract_text_from_pdf(pdf_path)
            extract_end_time = time.time()
            #print(text)  # print the raw text output (converted from pdf)
            print("Starting to call endpoint...")
            openai_start_time = time.time()
            response = None
            attempts = 0
            while attempts < MAX_RETRIES:
                if CLIENT_TYPE == 0:
                    response = call_azure(client, system_prompts, text)
                elif CLIENT_TYPE == 1:
                    response = call_openai(client, system_prompts, text)
                else: # CLIENT_TYPE == 2:
                    response = call_llama(client, system_prompts, text)
                if response is None: # we should really handle this properly, but often these are issues with azure/openai service, so let's wait a while and try again
                    time.sleep(RETRY_WAIT_DURATION)
                    response = call_openai(client, system_prompts, text)
                    #response = call_llama(client, system_prompts, text)
                else:
                    break
                attempts+=1
            if attempts < MAX_RETRIES:
                result = response.choices[0].message.content
                openai_end_time = time.time()
                print('\n\n##############################################')
                print(f"PDF extract finished in {extract_end_time - extract_start_time} seconds. Call finished in {openai_end_time - openai_start_time} seconds, reason: {response.choices[0].finish_reason}, choices: {len(response.choices)}")
                with open(GRADING_DIRECTORY+pdf+GRADING_SUFFIX, "w") as file:
                    file.write(result)
                print(result)
                update_ai_points(result, index, data) # llm don't really know math, so let's manually calculate the real point sum
            else:
                print("failed to create grading")
    end_time = time.time()
    print(f"Calls finished in {end_time - start_time} seconds.")

def update_ai_points(graded_text, index, data):
    total = 0
    lines = graded_text.splitlines()
    c1 = 0
    c2 = None
    c3 = None
    c4 = None
    c5 = None
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        elif parts and parts[0].replace('.', '', 1).replace('-', '', 1).isdigit():
            p = float(parts[0])
            total += p
            if c5 is not None:
                c5 += p
            elif c4 is not None:
                c4 += p
            elif c3 is not None:
                c3 += p
            elif c2 is not None:
                c2 += p
            else:
                c1 += p
        elif "Criteria 2" in parts[1]:
            c2 = 0
        elif "Criteria 3" in parts[1]:
            c3 = 0
        elif "Criteria 4" in parts[1]:
            c4 = 0
        elif "Criteria 5" in parts[1]:
            c5 = 0
        elif "### Summary" in parts[1]:
            break

    data.loc[index, ['ai_p_c1', 'ai_p_c2', 'ai_p_c3', 'ai_p_c4', 'ai_p_c5', 'ai_p_sum']] = [c1, c2, c3, c4, c5, total]
    print(f"Total (calculated) points: c1: {c1}, c2: {c2}, c3: {c3}, c4: {c4}. c5: {c5}, sum: {total}/8")

def create_azure_client():
    client = AzureOpenAI(
        api_key=AZURE_API_KEY,
        api_version=AZURE_API_VERSION,
        azure_endpoint=AZURE_ENDPOINT
    )
    print("azure client created.")
    return client

def create_llama_client():
    client = OpenAI(
        api_key = LLAMA_API_KEY,
        base_url = LLAMA_BASE_URL
    )
    print("llama client created.")
    return client

def create_openai_client():
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )
    print("openai client created.")
    return client

def main():
    data = read_data_file(POINTS_FILE)
    if CLIENT_TYPE == 0:
        client = create_azure_client()
    elif CLIENT_TYPE == 1:
        client = create_openai_client()
    else: # CLIENT_TYPE = 2:
        client = create_llama_client()
    run_tests(client, data)
    data.to_csv(POINTS_FILE, index=False)

if __name__ == "__main__":
    main()
