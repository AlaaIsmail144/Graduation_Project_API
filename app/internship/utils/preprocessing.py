import re
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer


def preprocess_text(text: str) -> str:
   
    if pd.isna(text) or not text:
        return ""
    # lowercase ---> remove urls ---> remove special characters ---> remove extra whitespace ---> tokenize ---> remove stopwords ---> lemmatize
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    custom_stops = {
        'internship', 'intern', 'will', 'also', 'work', 'working',
        'position', 'role', 'team', 'company', 'opportunity',
        'help', 'support', 'provide', 'ensure', 'use', 'using'
    }
    stop_words.update(custom_stops)
    
    tokens = [word for word in tokens if word not in stop_words and len(word) > 2]
    
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    return ' '.join(tokens)


def combine_text_fields(title: str, description: str, max_desc_length: int = 200) -> str:
    title = title or ""
    description = (description or "")[:max_desc_length]
    return f"{title} {description}".strip()