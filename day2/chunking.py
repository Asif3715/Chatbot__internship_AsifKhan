from langchain_text_splitters import RecursiveCharacterTextSplitter
import re

def chunk_fixed(text, size=300, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks

def chunk_sentences(text, sentences_per_chunk=3):
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        group = sentences[i:i + sentences_per_chunk]
        chunks.append(' '.join(group))
    return chunks

def chunk_recursive(text, size=300, overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=['\n\n', '\n', ' ', '']
    )
    return splitter.split_text(text)

def compare_strategies(text):
    strategies = {
        'Fixed-Size': chunk_fixed(text),
        'Sentence': chunk_sentences(text),
        'Recursive': chunk_recursive(text),
    }
    print('\n' + '='*55)
    print('CHUNKING STRATEGY COMPARISON')
    print('='*55)
    print(f'{"Strategy":<16} {"Chunks":>8} {"Avg Length":>12}')
    print('-'*55)
    for name, chunks in strategies.items():
        avg = sum(len(c) for c in chunks) // len(chunks) if chunks else 0
        print(f'{name:<16} {len(chunks):>8} {avg:>10} chars')
    print('='*55)
    print('\n--- First chunk of each strategy ---')
    for name, chunks in strategies.items():
        print(f'\n[{name}]')
        print(chunks[0] if chunks else '(empty)')

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')
    from day2.ingestion import load_document
    text = load_document('sample.pdf')
    print('Loaded', len(text), 'characters from sample.pdf')
    compare_strategies(text)
