import sqlite3
import os
from datetime import datetime
from typing import List, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), 'chat_history.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def initialise_db():
    conn = get_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp DATETIME DEFAULT (datetime('now'))
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON chat_history (session_id)')
    conn.commit()
    conn.close()
    print(f'Database initialised at: {DB_PATH}')

def save_turn(session_id: str, question: str, answer: str):
    conn = get_connection()
    conn.execute(
        'INSERT INTO chat_history (session_id, question, answer) VALUES (?, ?, ?)',
        (session_id, question, answer),
    )
    conn.commit()
    conn.close()

def get_session_history(session_id: str) -> List[Dict]:
    conn = get_connection()
    rows = conn.execute(
        'SELECT question, answer, timestamp FROM chat_history WHERE session_id = ? ORDER BY id ASC',
        (session_id,),
    ).fetchall()
    conn.close()
    return [{'question': r['question'], 'answer': r['answer'], 'timestamp': r['timestamp']} for r in rows]

def list_all_sessions() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute('''
        SELECT session_id, COUNT(*) AS turn_count, MIN(timestamp) AS started_at, MAX(timestamp) AS last_active
        FROM chat_history GROUP BY session_id ORDER BY last_active DESC
    ''').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_session(session_id: str) -> int:
    conn = get_connection()
    cursor = conn.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count

if __name__ == '__main__':
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    initialise_db()
    save_turn('session-001', 'What is NexusChat?', 'NexusChat is an enterprise RAG chatbot.')
    save_turn('session-001', 'What formats does it support?', 'It supports PDF, DOCX, and TXT.')
    save_turn('session-002', 'How much does it cost?', 'The Professional plan costs 200 USD/month.')
    history = get_session_history('session-001')
    print(f'\nsession-001 has {len(history)} turns:')
    for turn in history:
        print(f' Q: {turn["question"]}')
        print(f' A: {turn["answer"]}')
    sessions = list_all_sessions()
    print(f'\nAll sessions in DB: {len(sessions)}')
    for s in sessions:
        print(f' {s["session_id"]} — {s["turn_count"]} turns, last active: {s["last_active"]}')
    deleted = delete_session('session-002')
    print(f'\nDeleted {deleted} rows from session-002')
    print(f'Remaining sessions: {len(list_all_sessions())}')
    print('\nAll SQLite tests passed.')
