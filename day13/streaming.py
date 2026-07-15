import json
import os
import sys
import google.generativeai as genai

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from day4.generator import build_prompt

GENERATION_MODEL = 'models/gemini-3-flash-preview'


def stream_answer(question, retrieved_chunks):
    prompt = build_prompt(question, retrieved_chunks)
    model = genai.GenerativeModel(GENERATION_MODEL)
    response = model.generate_content(prompt, stream=True)
    full_text = ''

    for chunk in response:
        if chunk.text:
            full_text += chunk.text
            event = json.dumps({'token': chunk.text})
            yield f'data: {event}\n\n'

    sources = [
        {'source': c['source'], 'preview': c['text'][:150]}
        for c in retrieved_chunks
    ]
    yield f'data: {json.dumps({"sources": sources})}\n\n'
    yield f'data: {json.dumps({"done": True})}\n\n'
