import os
import fitz
from docx import Document
from pathlib import Path

def load_txt(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def load_pdf(path):
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    return ' '.join(pages)

def load_docx(path):
    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return ' '.join(paragraphs)

def load_document(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.txt':
        return load_txt(path)
    if ext == '.pdf':
        return load_pdf(path)
    if ext == '.docx':
        return load_docx(path)
    raise ValueError(f'Unsupported file type: {ext}. Supported: .txt .pdf .docx')

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent
    for filename in ['sample.txt', 'sample.pdf', 'sample.docx']:
        path = base_dir / filename
        print('--- Loading', filename, '---')
        text = load_document(str(path))
        print('Characters loaded:', len(text))
        print('Preview:', (text[:150] + '...') if text else '(empty)')
