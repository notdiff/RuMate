from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.vectorstores import FAISS
import warnings

import requests
import pandas as pd

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

warnings.filterwarnings("ignore")

### Подгружаем документацию
loader = DirectoryLoader(
    'full_docs/full_doc',
    glob="./*.md",
    loader_cls=TextLoader,
    show_progress=True,
    use_multithreading=True
)

documents = loader.load()
print(f'We have {len(documents)} pages in total')

### Правим сслыки в тексте
for page in range(len(documents)):
    page_content = documents[page].page_content
    page_content = page_content.replace('/help/', 'https://www.rustore.ru/help/')
    documents[page].page_content = page_content

### Разделяем текст только по главным заголовкам
headers_to_split_on = [
    ("#", "Header 1"),
]
markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)


all_splits = []

for doc in documents:
    md_header_splits = markdown_splitter.split_text(doc.page_content)
    for i in range(len(md_header_splits)):
        md_header_splits[i].metadata['source'] = doc.metadata['source'] # Сохраняем источник
    all_splits.extend(md_header_splits)

 ### Дополнительно разбиваем на чанки по 800 символов с перекрытием 500 символов
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=500
)

texts = text_splitter.split_documents(documents)
print(f'We have created {len(texts)} chunks')

### Модель для эмбеддингов
embeddings = HuggingFaceInstructEmbeddings(
    model_name='sentence-transformers/all-MiniLM-L6-v2',
    model_kwargs={"device": "cpu"}
)

### Вектоорная БД
vectordb = FAISS.load_local(
    'full_docs/faiss_index_hp',  # from output folder
    embeddings,
    allow_dangerous_deserialization=True
)

k = 10 # Число похожих чанков для ретривера
retriever_base = BM25Retriever.from_documents(texts, k=k) # Базовый ретривер
retriever_advanced = vectordb.as_retriever(search_kwargs={"k": k, "search_type": "similarity"}) # Ретривер на основе эмбеддингов
ensemble_retriever = EnsembleRetriever(retrievers=[retriever_base, retriever_advanced], weights=[0.5, 0.5], k=k) # Ансамбль ретриверов

# Промпт для YandexGPT
query = """
Ты получишь контекст и вопрос по нему, который касается магазина приложений RuStore.
Выведи ответ на вопрос, используя только контекст.
Ответ должен быть в markdown, сохрани изначальную структуру контекста, и отобрази максимально полный ответ.
Если ответа нет в контексте или вопрос не по теме магазина приложений, напиши 'уточните, пожалуйста, вопрос', не выдумывай ответ сам!!!
Например, вопрос 'как тебя зовут?' не относится к теме, а вот 'как мне выпустить приложение?' - относится.
"""

data = pd.read_csv('full_doc/labels.csv')


def yagpt_request(question, context):

    """
    Подаем запрос в YandexGPT, возвращаем ответ


    Args:
        question (str): Вопрос
        context (str): Контекст
        
    Returns:
        text (str): Ответ
        render (str): Источник
    """

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "" # Вставьте ваш api ключ
    }

    folder = # id папки

    ya_prompt = {
        "modelUri": f"gpt://{folder}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.0,
            "maxTokens": "1024"
        },
        "messages": [
            {
                "role": "system",
                "text": query
            },
            {
                "role": "user", "text":
    f"""Контекст:
    {context}

    Вопрос: {question}"""
            }
        ]
    }

    response = requests.post(url, headers=headers, json=ya_prompt)
    result = eval(response.text)

    return result['result']['alternatives'][0]['message']['text']


def get_source(names):
    # Получаем источники
    hrefs = data[data.filename.isin(names)][['title', 'URL']].values.tolist()
    render = '<br>'.join([f"[{t}]({l})" for t,l in hrefs])

    return render

def refactor_sim_search_res(question):
    # Финальный пайплайн
    retriever_ans_raw = ensemble_retriever.invoke(question, k=6) # Релевантные чанки из ретривера

    page_content = [i.page_content for i in retriever_ans_raw]
    sources = [i.metadata['source'] for i in retriever_ans_raw]
    sources = [i[i.rfind('/')+1:] for i in sources]

    render = get_source(sources)

    retriever_ans = '\n\n'.join(page_content)

    context = query.format(context=retriever_ans) # Что подаем в YandexGPT

    text = yagpt_request(question, context).replace('\n', '<br>') # Получаем ответ от YandexGPT
    text += f"""
    <br>**Источники:**<br>
    {render}
    """

    return text, render