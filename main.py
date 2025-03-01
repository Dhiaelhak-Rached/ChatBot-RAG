from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import requests
import json
from PyPDF2 import PdfReader
import re

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

all_questions = {}

# Path to the single PDF file
pdf_file_path = "pdf-file.pdf"

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    text = ""
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def clean_text(text):
    # Remove page numbers, dates, and other unwanted elements
    text = re.sub(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', '', text)  # Remove dates
    text = re.sub(r'\n+', ' ', text)  # Replace new lines with spaces
    text = re.sub(r'\s+', ' ', text)  # Remove multiple spaces
    text = text.strip()  # Trim spaces at the beginning and end
    return text

def split_into_chunks(text, chunk_size=200):
    """Split text into chunks of approximately chunk_size words."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    
    return chunks

def generate_questions_with_ollama(text_chunk):
    """Generate questions using Ollama's TinyLlama model"""
    prompt = f"""
    Based on the following text, generate a concise question that tests understanding of the content.
    Make sure the question is clear, focused, and ends with a question mark.
    
    Text: {text_chunk}
    
    Question:
    """
    
    # Call Ollama API
    response = requests.post('http://localhost:11434/api/generate', 
                           json={
                               "model": "tinyllama",
                               "prompt": prompt,
                               "stream": False
                           })
    
    if response.status_code == 200:
        result = response.json()
        return result['response'].strip()
    else:
        return None

def generate_questions_from_text(text):
    # Split text into manageable chunks
    chunks = split_into_chunks(text, chunk_size=150)
    
    # List to store generated questions
    questions = []
    
    # Use a subset of chunks to avoid too many questions
    for i, chunk in enumerate(chunks):
        if i % 3 != 0:  # Process every third chunk to reduce volume
            continue
            
        if len(chunk.strip()) < 50:  # Skip very short chunks
            continue
        
        # Generate question using Ollama
        question = generate_questions_with_ollama(chunk)
        
        # Add the generated question to the list
        if question and question.strip() not in questions:
            questions.append(question.strip())
            
        # Limit the number of questions
        if len(questions) >= 10:
            break

    return questions

def clean_and_format_questions(questions):
    formatted_questions = []

    for question in questions:
        # Limit the number of words to 10
        words = question.split()
        if len(words) > 10:
            question = " ".join(words[:10])

        # Ensure the question ends with "?"
        if not question.endswith('?'):
            question += "?"

        formatted_questions.append(question)

    return formatted_questions

@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')

@app.route('/date', methods=['GET'])
def get_date():
    # Check if the file exists
    if not os.path.exists(pdf_file_path):
        return jsonify({'error': 'PDF file not found'}), 404
    
    # Check if the file is a PDF
    if not pdf_file_path.endswith(".pdf"):
        return jsonify({'error': 'File is not a PDF'}), 400
        
    # Extract and clean the text
    text = extract_text_from_pdf(pdf_file_path)
    cleaned_text = clean_text(text)
    
    if len(cleaned_text) <= 10:
        return jsonify({'error': 'PDF does not contain enough usable text'}), 400
        
    # Generate questions based on the extracted text using Ollama
    questions = generate_questions_from_text(cleaned_text)
    
    # Apply the 10-word limit and add "?" if necessary
    formatted_questions = clean_and_format_questions(questions)
    
    # Store the questions in a dictionary
    all_questions = {os.path.basename(pdf_file_path): formatted_questions}
    
    return jsonify({'questions': all_questions})

@app.route('/upload', methods=['POST'])
def upload_pdf():
    global pdf_file_path
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if file and file.filename.endswith('.pdf'):
        # Save the uploaded file
        file_path = os.path.join('uploads', file.filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(file_path)
        pdf_file_path = file_path
        
        return jsonify({'success': True, 'filename': file.filename})
    else:
        return jsonify({'error': 'File must be a PDF'}), 400

if __name__ == '__main__':
    app.run(debug=True)
