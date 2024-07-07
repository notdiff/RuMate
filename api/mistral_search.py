Никита Угрюмов, [07.07.2024 10:20]
import warnings 
warnings.filterwarnings("ignore") 
 
import textwrap 
import time 
 
### prompts 
from langchain import PromptTemplate 
 
### vector stores 
from langchain.vectorstores import FAISS 
 
### HF pipeline for LLM 
from langchain_huggingface import HuggingFacePipeline 
 
### embeddings 
from langchain_community.embeddings import HuggingFaceInstructEmbeddings 
 
### retrievers 
from langchain.chains import RetrievalQA 
 
 
import torch 
import transformers 
from transformers import ( 
    AutoTokenizer, AutoModelForCausalLM, 
    BitsAndBytesConfig, 
    pipeline 
) 
 
from huggingface_hub import login 
 
 
HF_TOKEN = _ # Вставьте ваш токен HuggingFace 
login(HF_TOKEN) 
 
 
class CFG: 
 
    """ 
    Конфиг для инференса Mistral 
     
    Attributes: 
        model_name (str): Название модели 
        temperature (float): Температура ("креативность") во время генерации, в нашем случае важна точность, температура нулевая 
        top_p (float): Параметр для top-p семплирования 
        repetition_penalty (float): Наказание за повтор LLM 
         
         
        embeddings_model_repo (str): Путь к репозиторию модели для получения эмбеддингов текстов 
         
        k (int): Число чанков для ретривера 
    """ 
 
    # LLMs 
    model_name = 'mistral-7B' # wizardlm, llama2-7b-chat, llama2-13b-chat, mistral-7B 
    temperature = 0 
    top_p = 0.95 
    repetition_penalty = 1.15     
     
    # embeddings 
    embeddings_model_repo = 'sentence-transformers/all-MiniLM-L6-v2'     
 
    # similar passages 
    k = 6 
 
 
 
 
def get_model(model = CFG.model_name): 
 
    """ 
    Подгружает нужную модель и токенайзер, определяет максимальную длину в токенах 
 
    """ 
 
    print('\nDownloading model: ', model, '\n\n') 
 
    if model == 'mistral-7B': 
        model_repo = 'mistralai/Mistral-7B-v0.3' 
         
        tokenizer = AutoTokenizer.from_pretrained(model_repo) 
         
        bnb_config = BitsAndBytesConfig( 
            load_in_4bit = True, 
            bnb_4bit_quant_type = "nf4", 
            bnb_4bit_compute_dtype = torch.float16, 
            bnb_4bit_use_double_quant = True, 
        )         
 
        model = AutoModelForCausalLM.from_pretrained( 
            model_repo, 
            quantization_config = bnb_config, 
            device_map = 'auto', 
            low_cpu_mem_usage = True, 
        ) 
         
        max_len = 1024 
 
    else: 
        print("Not implemented model (tokenizer and backbone)") 
 
    return tokenizer, model, max_len 
 
 
 
 
tokenizer, model, max_len = get_model(model = CFG.model_name) 
model.eval() 
### hugging face pipeline 
pipe = pipeline( 
    task = "text-generation", 
    model = model, 
    tokenizer = tokenizer, 
    pad_token_id = tokenizer.eos_token_id, 
#     do_sample = True, 
    max_length = max_len, 
    temperature = CFG.temperature, 
    top_p = CFG.top_p, 
    repetition_penalty = CFG.repetition_penalty 
) 
 
 
llm = HuggingFacePipeline(pipeline = pipe) 
 
 
### Модель для эмбеддингов 
embeddings = HuggingFaceInstructEmbeddings( 
    model_name='sentence-transformers/all-MiniLM-L6-v2', 
    model_kwargs={"device": "cpu"} # Можете сменить на "cuda" 
) 
 
### Векторная база данных 
vectordb = FAISS.load_local( 
    'full_docs/faiss_index_hp', 
    embeddings, 
    allow_dangerous_deserialization=True 
)  
 
 
### Промпт 
 
prompt_template = """ 
Чтобы ответить на вопрос, используй только следующие фрагменты контекста. 
Если ответа нет в контексте скажи об этом. 
Ответ должен быть в markdown, сохрани изначальную структуру контекста включая ссылки и картинки, и отобрази максимально полный и развернутый ответ. 
 
Контекст: 
{context} 
 
Вопрос: {question} 
Ответ: 
""" 
 
 
PROMPT = PromptTemplate( 
    template = prompt_template,  
    input_variables = ["context", "question"] 
) 
 
### Ретривер 
 
retriever = vectordb.as_retriever(search_kwargs = {"k": CFG.k, "search_type" : "similarity"}) 
 
### Финальный пайплайн 
 
qa_chain = RetrievalQA.from_chain_type( 
    llm = llm,

Никита Угрюмов, [07.07.2024 10:20]
chain_type = "stuff", # map_reduce, map_rerank, stuff, refine 
    retriever = retriever,  
    chain_type_kwargs = {"prompt": PROMPT}, 
    return_source_documents = True, 
    verbose = False 
) 
def wrap_text_preserve_newlines(text, width=700): 
    # Split the input text into lines based on newline characters 
    lines = text.split('\n') 
 
    # Wrap each line individually 
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines] 
 
    # Join the wrapped lines back together using newline characters 
    wrapped_text = '\n'.join(wrapped_lines) 
 
    return wrapped_text 
 
 
def process_llm_response(llm_response): 
    # Пост-процессинг ответа LLM 
    ans = wrap_text_preserve_newlines(llm_response['result']) 
     
    sources_used = ' \n'.join( 
        [ 
            source.metadata['source'].split('/')[-1][:-4] 
            + ' - page: ' 
            + str(source.metadata['page']) 
            for source in llm_response['source_documents'] 
        ] 
    ) 
     
    ans = ans + '\n\nSources: \n' + sources_used 
    return ans 
 
def llm_ans(query): 
    # Ответ LLM 
    start = time.time() 
     
    llm_response = qa_chain.invoke(query) 
    ans = process_llm_response(llm_response) 
     
    end = time.time() 
 
    time_elapsed = int(round(end - start, 0)) 
    time_elapsed_str = f'\n\nTime elapsed: {time_elapsed} s' 
    return ans + time_elapsed_str 
 
 
def refactor_llm_ans(query): 
    return llm_ans(query)