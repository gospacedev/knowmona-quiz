import os
from together import Together
from dotenv import load_dotenv
import json
from .schemas import QuizSchematic

# For importing the private Together AI API key
load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

def infer_quiz(question_difficulty, tone, topic):

    instructions_prompt = f"""<s> [INST] Your are a great teacher and your task is to create 10 questions with 4 choices with a {question_difficulty} difficulty in a {tone} tone about {topic}, then create an answers. Index in JSON format, the questions as "Q#":"" to "Q#":"", the four choices as "choice_1" to "choice_4", and the answers as "choice_1" to "choice_4". WRITE NOTHING ELSE [/INST]"""

    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages=[{"role": "system", "content": instructions_prompt}],
        response_format={
            "type": "json_object",
            "schema": QuizSchematic.model_json_schema(),
        },
    )

    print(json.dumps(response.choices[0].message.content, indent=4))

    output = json.loads(response.choices[0].message.content)

    return output

print(infer_quiz("hard", "casual", "bananas"))