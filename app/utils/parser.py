from bs4 import BeautifulSoup

def clean_text(text):
    if not text: return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator='\n')
