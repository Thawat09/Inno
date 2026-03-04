from pythainlp.tokenize import word_tokenize

def thai_tokenizer(text):
    if not text:
        return []
    return [word for word in word_tokenize(text, engine='newmm') if word.strip()]