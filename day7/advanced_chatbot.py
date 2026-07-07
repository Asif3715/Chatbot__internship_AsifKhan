import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from day4.generator import generate_answer
from day5.memory_chatbot import rewrite_query
from day6.hybrid_retriever import HybridRetriever
from day7.reranker import rerank
from day7.query_decomposer import decompose_and_answer

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

DOCUMENTS = [
    'day2/sample.txt',
    'day2/sample.pdf',
    'day2/sample.docx',
    'day2/sample2.txt',
]

DECOMPOSE_THRESHOLD = 1


def run_advanced_chatbot():
    retriever = HybridRetriever()
    chat_history = []

    print('Building advanced index (hybrid: BM25 + dense)...')
    retriever.index(DOCUMENTS)

    print('\n' + '='*65)
    print('NexusChat Advanced is ready.')
    print('Supports: hybrid search, re-ranking, query decomposition, memory.')
    print("Type 'quit' to exit.")
    print('='*65)

    while True:
        print()
        question = input('You: ').strip()
        if not question:
            continue
        if question.lower() in ('quit', 'exit'):
            print('Goodbye!')
            break

        standalone = rewrite_query(question, chat_history)
        if standalone != question:
            print(f' (search query: "{standalone}")')

        result = decompose_and_answer(
            standalone, retriever, rerank, generate_answer
        )
        final_answer = result['final_answer']
        print(f'\nNexusChat: {final_answer}')
        chat_history.append({'question': question, 'answer': final_answer})


if __name__ == '__main__':
    run_advanced_chatbot()
