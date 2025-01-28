from typing import List, Dict

CHUNK_SIZE = 4000
OVERLAP_SIZE = 100

def chunk_text(text: str) -> List[dict]:
    chunks = []
    words = text.split()
    total_words = len(words)
    chunk_index = 0
    
    words_per_chunk = CHUNK_SIZE // 5
    
    for i in range(0, total_words, words_per_chunk):
        chunk_words = words[i:i + words_per_chunk + (OVERLAP_SIZE // 5)]
        if chunk_words:
            chunks.append({
                'text': ' '.join(chunk_words),
                'index': chunk_index,
                'start_position': i,
                'end_position': min(i + words_per_chunk, total_words)
            })
            chunk_index += 1
    
    return chunks