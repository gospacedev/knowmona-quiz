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
    
    res = service.cse().list(q=search_term, cx=cse_id, fields="items(link,snippet)", **kwargs).execute()
    
    # Create separate strings for links and snippets
    links = ""
    snippets = ""
    
    # Extract and append links and snippets separately
    for item in res['items']:
        links += f"{item['link']}\n"
        snippets += f"{item.get('snippet', 'No snippet available')}\n"
    
    return snippets.strip(), links.strip()

def infer_quiz_json(form, uploaded_texts=""):
    if form.is_valid():
        question_difficulty = form.cleaned_data.get('question_difficulty')
        if question_difficulty == "" or question_difficulty == None:
            question_difficulty = "average"

        tone = form.cleaned_data.get('tone')
        if tone == "" or tone == None:
            tone = "casual"

        topic = form.cleaned_data.get('topic')

        external_data, external_reference = get_external_data(topic, google_api_key, search_engine_id, num=5)

        if uploaded_texts == "":
            uploaded_texts = "No user inputted information"

        instructions_prompt = f"""<s> [INST] Your are a great teacher and your task is to create 10 questions with 4 choices with a {question_difficulty} difficulty in a {tone} tone about {topic}, then create an answers. Index in JSON format, the questions as "Q#":"" to "Q#":"", the four choices as "choice_1" to "choice_4", the answers as "choice_1" to "choice_4", and a one-sentence explanation. WRITE NOTHING ELSE DO AND NOT REPEAT QUESTIONS Ulitize some of these information from the Internet:  """ + external_data + """\nUser inputted information: """ + uploaded_texts + f"""[/INST]"""

        response = client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            temperature=0.3,
            repetition_penalty=1,
            messages=[{"role": "system", "content": instructions_prompt}],
            response_format={
                "type": "json_object",
                "schema": QuizSchematic.model_json_schema(),
            },
        )

        output = response.choices[0].message.content

        print(json.dumps(output, indent=4))

        return json.loads(output), external_reference
    else:
        return {
            "status": "error",
            "errors": form.errors
        }


from django.db import transaction

def save_quiz_from_json(quiz_data, external_reference, quiz):
    """
    Optimized version of quiz data loader using transaction.atomic() and get_or_create
    to minimize database operations and ensure data consistency.
    """
    # Use transaction.atomic() to ensure all operations succeed or fail together
    with transaction.atomic():
        # Prepare all data structures first
        questions_data = []
        explanations_data = []
        choices_data = []
        
        # Pre-allocate lists for better memory efficiency
        for question_num in range(1, 11):
            question_key = f"Q{question_num}"
            question_data = quiz_data.get(question_key)
            
            if not question_data:
                continue

            question = Question(
                quiz=quiz,
                text=question_data["question"]
            )
            questions_data.append(question)

            explanations_data.append({
                'text': question_data["explanation"],
                'question': question  # Will be updated after bulk create
            })

            correct_answer = question_data.get("answer")
            if correct_answer:
                for i in range(1, 5):
                    choice_key = f"choice_{i}"
                    choice_text = question_data.get(choice_key)
                    
                    if choice_text:
                        choices_data.append({
                            'text': choice_text,
                            'is_correct': (choice_key == correct_answer),
                            'question': question  # Will be updated after bulk create
                        })

        # Bulk create questions and get their IDs
        if questions_data:
            questions = Question.objects.bulk_create(
                questions_data,
                batch_size=100,  # Adjust based on your database
                ignore_conflicts=True
            )

            # Create explanations with correct question references
            if explanations_data:
                Explanation.objects.bulk_create([
                    Explanation(
                        question=questions[i],
                        text=exp_data['text']
                    )
                    for i, exp_data in enumerate(explanations_data)
                ], batch_size=100)

            # Create choices with correct question references
            if choices_data:
                # Map the original question objects to their created counterparts
                question_map = {q_data: q_created 
                              for q_data, q_created in zip(questions_data, questions)}
                
                Choice.objects.bulk_create([
                    Choice(
                        question=question_map[choice_data['question']],
                        text=choice_data['text'],
                        is_correct=choice_data['is_correct']
                    )
                    for choice_data in choices_data
                ], batch_size=100)

        # Create reference using get_or_create to avoid duplicates
        Reference.objects.get_or_create(
            quiz=quiz,
            defaults={'text': external_reference}
        )
