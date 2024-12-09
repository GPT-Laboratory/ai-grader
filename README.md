# ai-grader

Implementation for an AI grader of group assignments (essays).

Check grader.py for Python requirements.

The script will read the given POINTS_FILE and generate grading for each entry (pdf) listed in the file using the provided instructions. The POINTS_FILE will be updated with the generated grading (points) and related textual feedback for the works will be produced in the GRADING_DIRECTORY. See further information from below.

The files included:
- grader.py
	- The main script file
	- It includes examples for running the script for Azure, OpenAI and LLama (ollama/OpenAI API specification) implementations
- points_template.csv
	- List of (pdf) files to grade
	- Columns:
		- pdf = pdf files to grade
		- student_numder = student number(s) (optional)
		- p_c1, p_c2, p_c3, p_c4 and p_c5 = points awarded by a human reviewer, can be used for reference, are not actually used by the script
		- p_sum and p_sum_moodle = the total sum of the previous individual points and the final (rounded) grade (p_sum_moodle), as given by a human reviewer. Similarly as the previous columns, there are not used by the grader script, but can be used for reference
		- ai_p_c1, ai_p_c2, ai_p_c3, ai_p_c4, ai_p_c5 = the grading (points) as awarded (generated) by AI
		- ai_p_sum = total sum of the previous AI generated points
- instructions.md
	- The grading instructions
	- You can modify these for AI, but in general, to compare human and AI performance and grading quality, these instructions should be if not identical, then at least similar
	- Criteria 1 - 5 match the ai_p_c1 - ai_p_c5 columns of points_template.csv
- assignment.pdf
	- Assignment instructions given to students
	- Note that the URL links given in the assignment instructions are not guaranteed to work anymore, but they did work when the instructions were given to students. In any case, for this grader implementation the links are irrelevant.
	
	
Important variables in grader.py:
- PDF_DIRECTORY = Location of the student works (pdf files)
- GRADING_DIRECTORY = Location where the final gradings will be produced
- POINTS_FILE = Name of you points file (list of student works to grade)
- ASSIGNMENT_SPECIFICATION = Name of your assignment specification file
	- Note: you don't always need to add the assignment specification file, the AI can generate grading even without it. Whether it makes any difference depends on the case, and the model/implementation used. You should verify the results with your use case.
	- Check the create_system_prompt() function's line prompts.append(f"Here are the assignment instructions given to the students: {extract_text_from_pdf(ASSIGNMENT_SPECIFICATION)}")
- GRADING_INSTRUCTIONS = Name of your grading instructions file
- AZURE_MODEL_ENGINE = If you are using Azure, add model deployment here
- AZURE_API_KEY= If you are using Azure, add API key here
- AZURE_ENDPOINT = If you are using Azure, add end point url here
- OPENAI_API_KEY = If you are using OpenAI, add API key here
- OPENAI_MODEL_ENGINE = If you are using OpenAI, add model name here
- LLAMA_API_KEY = "token-not-needed-right-now" or your Llama/Ollama API KEY
- LLAMA_BASE_URL = If you are using Llama, add your base URL here
- LLAMA_MODEL = Llama/Ollama model, e.g., "tgi"
- CLIENT_TYPE = The implementation to use, 0 = azure, 1 = openai, 2 = ollama

No actual student works or grading data are included in this repository to preserve the copyrights and anonymity of students.

