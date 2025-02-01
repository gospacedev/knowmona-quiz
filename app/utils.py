import os
import json
from together import Together
from dotenv import load_dotenv
from .schemas import QuizSchematic
from .models import Question, Choice, Reference, Explanation
from googleapiclient.discovery import build
from django.db import transaction


load_dotenv()

import os
import json
from itertools import zip_longest
from together import Together
from django.db import transaction
from googleapiclient.discovery import build

# Environment setup optimized for direct access
client = Together(api_key=os.environ["TOGETHER_API_KEY"])
GOOGLE_CONFIG = (os.environ["GOOGLE_API_KEY"], os.environ["SEARCH_ENGINE_ID"])

def get_external_data(search_term, num=3):
    """Vectorized data processing with pre-allocated memory"""
    service = build("customsearch", "v1", developerKey=GOOGLE_CONFIG[0])
    res = service.cse().list(
        q=search_term, cx=GOOGLE_CONFIG[1], num=num,
        fields="items(link,snippet)"
    ).execute()
    
    items = res.get('items', [])[:num]
    return (
        '\n'.join(i.get('snippet', '') for i in items),
        '\n'.join(i['link'] for i in items)
    )

def infer_quiz_json(form, uploaded_texts=""):
    """Optimized prompt engineering with pre-structured templating"""
    if not form.is_valid():
        return {"errors": form.errors.get_json_data()}, 400

    data = form.cleaned_data
    topic = data['topic']
    snippets, links = get_external_data(topic)
    
    PROMPT_TEMPLATE = (
        f"<s>[INST]Generate 10 {data.get('question_difficulty', 'average')}-difficulty "
        f"{data.get('tone', 'casual')} MCQs about {topic}. JSON format: "
        "Q# {question, choices[4], answer, explanation}. Sources: {snippets}\n"
        f"User inputs: {uploaded_texts or 'None'}[/INST]"
    ).replace('{snippets}', snippets[:2000])  # Truncate to prevent token overflow

    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        messages=[{"role": "system", "content": PROMPT_TEMPLATE}],
        max_tokens=2048,
        temperature=0.7,
        response_format={"type": "json_object", "schema": QuizSchematic.model_json_schema()},
    )

    return json.loads(response.choices[0].message.content), links

@transaction.atomic
def save_quiz_from_json(quiz_data, external_reference, quiz):
    """Batched vectorized database operations with direct field mapping"""
    # Pre-allocate memory for all objects
    questions = [None] * 10
    explanations = []
    choices = []
    
    for idx in range(10):
        q_key = f"Q{idx+1}"
        if not (q_data := quiz_data.get(q_key)):
            continue
            
        # Direct field mapping without intermediate objects
        questions[idx] = Question(quiz=quiz, text=q_data["question"])
        explanations.append((q_data["explanation"], idx))
        
        # Vectorized choice processing
        correct = q_data["answer"]
        choices.extend(
            (q_data[f"choice_{i}"], f"choice_{i}" == correct, idx)
            for i in range(1, 5)
        )

    # Bulk database operations
    Question.objects.bulk_create(filter(None, questions), batch_size=1000)
    q_objs = Question.objects.filter(quiz=quiz).order_by('id')
    
    # Batch explanation creation using database-side sorting
    Explanation.objects.bulk_create([
        Explanation(text=text, question=q_objs[idx])
        for text, idx in explanations
    ], batch_size=1000)
    
    # Batch choice creation with direct index mapping
    Choice.objects.bulk_create([
        Choice(text=text, is_correct=correct, question=q_objs[idx])
        for text, correct, idx in choices
    ], batch_size=1000)

    # Atomic reference update
    Reference.objects.update_or_create(quiz=quiz, defaults={'text': external_reference})
