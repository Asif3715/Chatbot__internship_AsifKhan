import os
import sys
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

JUDGE_MODEL = 'models/gemini-3-flash-preview'

def _call_judge(prompt):
    model = genai.GenerativeModel(JUDGE_MODEL)
    response = model.generate_content(prompt)
    raw = response.text.strip()
    matches = re.findall(r'\d+\.\d+|\d+', raw)
    if not matches:
        return 0.0
    score = float(matches[0])
    return max(0.0, min(1.0, score))

def score_faithfulness(question, answer, context_chunks):
    context_text = '\n\n'.join(c['text'] for c in context_chunks)
    prompt = f'''You are an expert evaluator assessing RAG system quality.
Score the FAITHFULNESS of the answer below on a scale from 0.0 to 1.0.
FAITHFULNESS definition: Every factual claim in the answer must be
directly supported by the provided CONTEXT. Claims not found in the
context reduce the score. A score of 1.0 means every claim is grounded.
A score of 0.0 means the answer contains entirely ungrounded claims.

CONTEXT:
{context_text}

QUESTION: {question}
ANSWER: {answer}

Output ONLY a single float between 0.0 and 1.0. Nothing else.
Score:'''
    return _call_judge(prompt)

def score_answer_relevance(question, answer):
    prompt = f'''You are an expert evaluator assessing RAG system quality.
Score the ANSWER RELEVANCE of the answer below on a scale from 0.0 to 1.0.
ANSWER RELEVANCE definition: Does the answer directly address the question?
Ignore whether the answer is factually correct — only judge whether it
is on-topic and responds to what was asked. A complete, on-topic answer
scores 1.0. An off-topic or evasive answer scores close to 0.0.

QUESTION: {question}
ANSWER: {answer}

Output ONLY a single float between 0.0 and 1.0. Nothing else.
Score:'''
    return _call_judge(prompt)

def score_context_recall(question, context_chunks, ground_truth):
    context_text = '\n\n'.join(c['text'] for c in context_chunks)
    prompt = f'''You are an expert evaluator assessing RAG system quality.
Score the CONTEXT RECALL on a scale from 0.0 to 1.0.
CONTEXT RECALL definition: Given the GROUND TRUTH answer, does the
retrieved CONTEXT contain all the information needed to produce it?
A score of 1.0 means the context is sufficient to derive the ground truth.
A score of 0.0 means the context is missing critical information.

QUESTION: {question}
GROUND TRUTH ANSWER: {ground_truth}
RETRIEVED CONTEXT:
{context_text}

Output ONLY a single float between 0.0 and 1.0. Nothing else.
Score:'''
    return _call_judge(prompt)

def evaluate_single(question, answer, context_chunks, ground_truth):
    faithfulness = score_faithfulness(question, answer, context_chunks)
    answer_relevance = score_answer_relevance(question, answer)
    context_recall = score_context_recall(question, context_chunks, ground_truth)
    mean_score = round((faithfulness + answer_relevance + context_recall) / 3, 4)
    return {
        'faithfulness': round(faithfulness, 4),
        'answer_relevance': round(answer_relevance, 4),
        'context_recall': round(context_recall, 4),
        'mean': mean_score,
    }

def evaluate_dataset(chatbot_name, test_cases, retrieve_fn, generate_fn):
    print(f'\nEvaluating: {chatbot_name}')
    print(f'Test cases: {len(test_cases)}')
    print('-' * 50)
    all_scores = []
    for i, case in enumerate(test_cases, 1):
        question = case['question']
        ground_truth = case['ground_truth']
        chunks = retrieve_fn(question)
        answer = generate_fn(question, chunks)
        scores = evaluate_single(question, answer, chunks, ground_truth)
        all_scores.append(scores)
        q_display = question[:50] + '...' if len(question) > 50 else question
        print(f' [{i}/{len(test_cases)}] Q: {q_display}')
        print(f' faithfulness={scores["faithfulness"]:.2f} relevance={scores["answer_relevance"]:.2f} recall={scores["context_recall"]:.2f} mean={scores["mean"]:.2f}')
    avg = {
        'chatbot': chatbot_name,
        'faithfulness': round(sum(s['faithfulness'] for s in all_scores) / len(all_scores), 4),
        'answer_relevance': round(sum(s['answer_relevance'] for s in all_scores) / len(all_scores), 4),
        'context_recall': round(sum(s['context_recall'] for s in all_scores) / len(all_scores), 4),
        'mean': round(sum(s['mean'] for s in all_scores) / len(all_scores), 4),
    }
    print(f'\n AVERAGES -> faithfulness={avg["faithfulness"]:.4f} relevance={avg["answer_relevance"]:.4f} recall={avg["context_recall"]:.4f} MEAN={avg["mean"]:.4f}')
    return avg

if __name__ == '__main__':
    test_question = 'What file formats does NexusChat support?'
    faithful_answer = 'NexusChat supports PDF, DOCX, and TXT file formats.'
    hallucinated_answer = 'NexusChat supports PDF, DOCX, TXT, CSV, XLSX, and MP3 files.'
    context = [
        {'text': 'NexusChat supports PDF, DOCX, and TXT document formats for ingestion.', 'source': 'sample.pdf'},
    ]
    ground_truth = 'NexusChat supports PDF, DOCX, and TXT formats.'
    print('--- Evaluating faithful answer ---')
    s1 = evaluate_single(test_question, faithful_answer, context, ground_truth)
    print(f' Faithfulness: {s1["faithfulness"]}')
    print(f' Answer Relevance: {s1["answer_relevance"]}')
    print(f' Context Recall: {s1["context_recall"]}')
    print(f' Mean: {s1["mean"]}')
    print('\n--- Evaluating hallucinated answer ---')
    s2 = evaluate_single(test_question, hallucinated_answer, context, ground_truth)
    print(f' Faithfulness: {s2["faithfulness"]}')
    print(f' Answer Relevance: {s2["answer_relevance"]}')
    print(f' Context Recall: {s2["context_recall"]}')
    print(f' Mean: {s2["mean"]}')
    print('\n--- Key check ---')
    print(f'Faithful answer faithfulness score: {s1["faithfulness"]:.2f}')
    print(f'Hallucinated answer faithfulness score: {s2["faithfulness"]:.2f}')
    if s1['faithfulness'] > s2['faithfulness']:
        print('PASS: Faithful answer scored higher on faithfulness.')
    else:
        print('REVIEW NEEDED: Scores did not separate as expected.')
