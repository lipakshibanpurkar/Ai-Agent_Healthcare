from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import OpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_text_from_file(file_path):
    text = ""
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
        elif ext == ".docx":
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(file_path)
            text += df.to_string()
        elif ext == ".csv":
            df = pd.read_csv(file_path)
            text += df.to_string()
        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8") as f:
                text += f.read()
        else:
            text = "Unsupported file type."
    except Exception as e:
        text = f"Error reading file: {str(e)}"

    return text

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', result=None)

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    uploaded_files = request.files.getlist('files')

    combined_text = ""
    for file in uploaded_files:
        if file.filename:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            extracted = extract_text_from_file(file_path)
            combined_text += f"\n--- {filename} ---\n{extracted}\n"

    result = {
        "query": query,
        "document_snippet": combined_text[:2000],  # Limit output to 2000 characters
        "timestamp": datetime.now().strftime("%d/%m/%Y, %I:%M:%S %p")
    }

    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
