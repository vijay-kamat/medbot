import os
import time
import random
import requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

DB_DIR = "./statpearls_chroma_db"

# 50 Direct Clinical Article Links (Bypassing Search)
DIRECT_LINKS = [
    {"title": "Tuberculosis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK441916/"},
    {"title": "Pneumonia", "url": "https://www.ncbi.nlm.nih.gov/books/NBK526084/"},
    {"title": "Asthma", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430901/"},
    {"title": "COPD", "url": "https://www.ncbi.nlm.nih.gov/books/NBK559281/"},
    {"title": "Pulmonary Embolism", "url": "https://www.ncbi.nlm.nih.gov/books/NBK441997/"},
    {"title": "Hypertension", "url": "https://www.ncbi.nlm.nih.gov/books/NBK482460/"},
    {"title": "Heart Failure", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430873/"},
    {"title": "Myocardial Infarction", "url": "https://www.ncbi.nlm.nih.gov/books/NBK537076/"},
    {"title": "Atrial Fibrillation", "url": "https://www.ncbi.nlm.nih.gov/books/NBK526072/"},
    {"title": "Stroke", "url": "https://www.ncbi.nlm.nih.gov/books/NBK535369/"},
    {"title": "Diabetes Type 2", "url": "https://www.ncbi.nlm.nih.gov/books/NBK513253/"},
    {"title": "Sepsis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430802/"},
    {"title": "Anemia", "url": "https://www.ncbi.nlm.nih.gov/books/NBK499994/"},
    {"title": "Liver Cirrhosis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK482419/"},
    {"title": "Pancreatitis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK541002/"},
    {"title": "Appendicitis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK493163/"},
    {"title": "Cholecystitis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK525959/"},
    {"title": "Hypothyroidism", "url": "https://www.ncbi.nlm.nih.gov/books/NBK519536/"},
    {"title": "Hyperthyroidism", "url": "https://www.ncbi.nlm.nih.gov/books/NBK537053/"},
    {"title": "Meningitis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK459360/"},
    {"title": "Multiple Sclerosis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK499849/"},
    {"title": "Parkinson Disease", "url": "https://www.ncbi.nlm.nih.gov/books/NBK470554/"},
    {"title": "Alzheimer Disease", "url": "https://www.ncbi.nlm.nih.gov/books/NBK499922/"},
    {"title": "Crohn Disease", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430664/"},
    {"title": "Ulcerative Colitis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK459282/"},
    {"title": "Rheumatoid Arthritis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK441999/"},
    {"title": "Pneumothorax", "url": "https://www.ncbi.nlm.nih.gov/books/NBK441885/"},
    {"title": "Sarcoidosis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK482242/"},
    {"title": "Aortic Stenosis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430857/"},
    {"title": "Deep Vein Thrombosis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK507708/"},
    {"title": "Infective Endocarditis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430769/"},
    {"title": "Pericarditis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK525964/"},
    {"title": "Peptic Ulcer Disease", "url": "https://www.ncbi.nlm.nih.gov/books/NBK534792/"},
    {"title": "Celiac Disease", "url": "https://www.ncbi.nlm.nih.gov/books/NBK441900/"},
    {"title": "Hepatitis B", "url": "https://www.ncbi.nlm.nih.gov/books/NBK470481/"},
    {"title": "Hepatitis C", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430897/"},
    {"title": "Addison Disease", "url": "https://www.ncbi.nlm.nih.gov/books/NBK441994/"},
    {"title": "Cushing Syndrome", "url": "https://www.ncbi.nlm.nih.gov/books/NBK470218/"},
    {"title": "Hypercalcemia", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430714/"},
    {"title": "Epilepsy", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430765/"},
    {"title": "Migraine Headache", "url": "https://www.ncbi.nlm.nih.gov/books/NBK560787/"},
    {"title": "Acute Kidney Injury", "url": "https://www.ncbi.nlm.nih.gov/books/NBK513297/"},
    {"title": "Chronic Kidney Disease", "url": "https://www.ncbi.nlm.nih.gov/books/NBK535404/"},
    {"title": "Pyelonephritis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK545204/"},
    {"title": "Iron Deficiency Anemia", "url": "https://www.ncbi.nlm.nih.gov/books/NBK448065/"},
    {"title": "Osteoarthritis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK482329/"},
    {"title": "Gout", "url": "https://www.ncbi.nlm.nih.gov/books/NBK430856/"},
    {"title": "Psoriasis", "url": "https://www.ncbi.nlm.nih.gov/books/NBK448194/"},
    {"title": "Lung Cancer", "url": "https://www.ncbi.nlm.nih.gov/books/NBK482357/"},
    {"title": "Pulmonary Hypertension", "url": "https://www.ncbi.nlm.nih.gov/books/NBK482463/"}
]

def scrape_article(url, expected_title):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"[-] Blocked on {expected_title} (Status: {response.status_code})")
            return None
            
        soup = BeautifulSoup(response.content, "html.parser")
        # Clean UI
        for nav in soup.find_all(["ul", "div"], class_=["toc", "bk_noprnt"]): nav.decompose()
        
        parsed_text = f"Disease: {expected_title}\n\n"
        target_sections = ["introduction", "etiology", "epidemiology", "pathophysiology", 
                           "history and physical", "evaluation", "treatment", "differential diagnosis"]
        
        found = False
        for header in soup.find_all(['h2', 'h3']):
            if any(t in header.text.lower() for t in target_sections):
                parsed_text += f"--- {header.text.strip().upper()} ---\n"
                for sib in header.find_next_siblings():
                    if sib.name in ['h1', 'h2', 'h3']: break
                    if sib.name == 'p': 
                        parsed_text += sib.text.strip() + " "
                        found = True
                parsed_text += "\n\n"
        return {"text": parsed_text, "metadata": {"source": url, "title": expected_title}} if found else None
    except Exception as e:
        print(f"[-] Error scraping {expected_title}: {e}")
        return None

def main():
    print(f"[*] Initializing Pipeline...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    
    success_count = 0
    start_time = time.time()

    print(f"[*] Processing {len(DIRECT_LINKS)} clinical articles...")
    for i, item in enumerate(DIRECT_LINKS):
        print(f"[{i+1}/{len(DIRECT_LINKS)}] Scraping: {item['title']}...", end="\r")
        
        data = scrape_article(item['url'], item['title'])
        if data:
            chunks = splitter.create_documents([data["text"]], metadatas=[data["metadata"]])
            Chroma.from_documents(chunks, embeddings, persist_directory=DB_DIR)
            success_count += 1
        
        # Be very polite to avoid IP ban
        time.sleep(random.uniform(2.0, 5.0))

    end_time = time.time()
    print(f"\n[***] FINISHED. Added {success_count} diseases in {round((end_time-start_time)/60, 2)} minutes.")

if __name__ == "__main__":
    main()