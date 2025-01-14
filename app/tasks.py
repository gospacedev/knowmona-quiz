from celery import shared_task
import os
from .models import UploadedFile, Quiz
from .utils import infer_quiz_json, save_quiz_from_json
from PyPDF2 import PdfReader
from docx import Document

@shared_task
def process_files_and_create_quiz(quiz_id, file_ids, form_data):
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        
        # Extract relevant data from form_data, if needed
        difficulty = form_data.get('question_difficulty', 'Average')
        tone = form_data.get('tone', 'Casual')

        uploaded_files = UploadedFile.objects.filter(id__in=file_ids)

        uploaded_texts = []  # Extract text from files
        for uploaded_file in uploaded_files:
            file_handle = uploaded_file.file.open()
            file_extension = os.path.splitext(uploaded_file.file.name)[1].lower()

            if file_extension == '.txt':
                uploaded_texts.append(file_handle.read().decode('utf-8'))
            elif file_extension == '.pdf':
                reader = PdfReader(file_handle)
                uploaded_texts.append(''.join(page.extract_text() for page in reader.pages))
            elif file_extension == '.docx':
                doc = Document(file_handle)
                uploaded_texts.append('\n'.join(p.text for p in doc.paragraphs))

            file_handle.close()

        # Now use the extracted texts and the form data for quiz generation
        json_output, external_reference = infer_quiz_json(difficulty, "\n".join(uploaded_texts))
        save_quiz_from_json(json_output, external_reference, quiz)

    except Exception as e:
        raise Exception(f"Error processing files and creating quiz: {e}")
