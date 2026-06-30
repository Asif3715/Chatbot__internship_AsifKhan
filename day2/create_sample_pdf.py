import fitz
from pathlib import Path

base_dir = Path(__file__).resolve().parent
doc = fitz.open()
page = doc.new_page()
text_lines = [
    'NexusChat Product Overview',
    '',
    'NexusChat is an enterprise RAG chatbot that answers questions from your documents.',
    'It supports PDF, DOCX, and TXT file formats.',
    'Documents are chunked, embedded, and stored in a vector database.',
    'Users can ask natural language questions and receive cited answers.',
    'The system is built on Google Gemini and ChromaDB.',
]
y = 72
for line in text_lines:
    page.insert_text((72, y), line, fontsize=12)
    y += 20
doc.save(base_dir / 'sample.pdf')
print('sample.pdf created successfully')
