import os
import json
from together import Together
from dotenv import load_dotenv
from .schemas import QuizSchematic
from .models import Question, Choice, Reference, Explanation
from googleapiclient.discovery import build


load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))
google_api_key = os.getenv("GOOGLE_API_KEY")
search_engine_id = os.getenv("SEARCH_ENGINE_ID")


def get_external_data(search_term, api_key, cse_id, **kwargs):

    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    
    # Create separate strings for links and snippets
    links = ""
    snippets = ""
    
    # Extract and append links and snippets separately
    for item in res['items']:
        links += f"{item['link']}\n"
        snippets += f"{item.get('snippet', 'No snippet available')}\n"
    
    return snippets.strip(), links.strip()

def infer_quiz_json(form):
    if form.is_valid():
        question_difficulty = form.cleaned_data.get('question_difficulty')
        if question_difficulty == "" or question_difficulty == None:
            question_difficulty = "average"

        tone = form.cleaned_data.get('tone')
        if tone == "" or tone == None:
            tone = "casual"

        topic = form.cleaned_data.get('topic')

        external_data, external_reference = get_external_data(topic, google_api_key, search_engine_id, num=10)

        instructions_prompt = f"""<s> [INST] Your are a great teacher and your task is to create 10 questions with 4 choices with a {question_difficulty} difficulty in a {tone} tone about {topic}, then create an answers. Index in JSON format, the questions as "Q#":"" to "Q#":"", the four choices as "choice_1" to "choice_4", the answers as "choice_1" to "choice_4", and a one-sentence explanation. WRITE NOTHING ELSE DO AND NOT REPEAT QUESTIONS Please ulitize these information: """ + external_data + f"""[/INST]"""

        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[{"role": "system", "content": instructions_prompt}],
            response_format={
                "type": "json_object",
                "schema": QuizSchematic.model_json_schema(),
            },
        )

        output = response.choices[0].message.content

        print(f"Raw Instruction Prompt{instructions_prompt}\n\n")
        print(json.loads(output))

        return json.loads(output), external_reference
    else:
        return {
            "status": "error",
            "errors": form.errors
        }


def save_quiz_from_json(quiz_data, external_reference, quiz):

    for question_num in range(1, 11):
        question_key = f"Q{question_num}"

        question_data = quiz_data.get(question_key)
        if not question_data:
            continue

        question = Question.objects.create(
            quiz=quiz,
            text=question_data["question"]
        )
        print(f"Created Question: {question.text}")

        explanation = Explanation.objects.create(
            question=question,
            text=question_data["explanation"]
        )
        print(f"Created Explanation: {explanation.text}")

        correct_answer = question_data.get("answer")
        if not correct_answer:
            continue  # Skip if no answer is found

        choice_keys = [f"choice_{i}" for i in range(1, 5)]
        for choice_key in choice_keys:
            choice_text = question_data.get(choice_key)
            if not choice_text:
                continue

            is_correct = (choice_key == correct_answer)

            Choice.objects.create(
                question=question,
                text=choice_text,
                is_correct=is_correct
            )
            print(f"Created Choice: {choice_text} - Correct: {is_correct}")

    Reference.objects.create(
        quiz=quiz,
        text=external_reference
    )
