from celery import shared_task
from django.core.files.storage import default_storage
from docx import Document
from PyPDF2 import PdfReader
import os
from .models import Quiz, UploadedFile
from .utils import infer_quiz_json, save_quiz_from_json

@shared_task
def process_uploaded_file(file_id):
    uploaded_file = UploadedFile.objects.get(id=file_id)
    try:
        file_path = uploaded_file.file.path
        file_extension = os.path.splitext(uploaded_file.file.name)[1].lower()
        
        with default_storage.open(uploaded_file.file.name, 'rb') as file_handle:
            if file_extension == '.txt':
                processed_text = file_handle.read().decode('utf-8')
            elif file_extension == '.pdf':
                reader = PdfReader(file_handle)
                processed_text = ''.join(page.extract_text() for page in reader.pages)
            elif file_extension == '.docx':
                doc = Document(file_handle)
                processed_text = '\n'.join(p.text for p in doc.paragraphs)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        
        uploaded_file.processed_text = processed_text
        uploaded_file.status = 'complete'
        uploaded_file.save()
        return True
        
    except Exception as e:
        uploaded_file.status = 'error'
        uploaded_file.save()
        quiz = uploaded_file.quiz
        quiz.status = 'error'
        quiz.error_message = str(e)
        quiz.save()
        raise

@shared_task
def create_quiz(quiz_id):
    quiz = Quiz.objects.get(id=quiz_id)
    try:
        # Combine all processed texts
        uploaded_files = quiz.files.filter(status='complete')
        combined_text = '\n'.join(f.processed_text for f in uploaded_files)
        
        # Your quiz creation logic here
        json_output, external_reference = infer_quiz_json({
            'question_difficulty': quiz.question_difficulty,
            'tone': quiz.tone
        }, combined_text)
        
        save_quiz_from_json(json_output, external_reference, quiz)
        
        quiz.status = 'complete'
        quiz.save()
        return quiz.id
        
    except Exception as e:
        quiz.status = 'error'
        quiz.error_message = str(e)
        quiz.save()
        raise