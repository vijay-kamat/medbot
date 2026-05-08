# 🩺 Clinical Intelligence System (CIS)

A **multi-agent diagnostic retrieval engine** that leverages evidence-based clinical guidelines and AI to assist in differential diagnosis. The system retrieves clinically relevant information from StatPearls and uses large language models (LLM) to generate evidence-grounded diagnostic hypotheses with built-in hallucination detection and peer review.

## ✨ Features

### 1. **Evidence-Based Retrieval**
- Scrapes and indexes 50+ clinical articles from StatPearls (NCBI)
- Stores content in a vector database (ChromaDB) using semantic embeddings
- Retrieves the most clinically relevant sources based on patient symptoms

### 2. **Multi-Agent Diagnostic Pipeline**
- **Agent A (Diagnosis Generator)**: Generates differential diagnoses strictly based on retrieved guidelines
- **Agent B (Auditor & Peer Reviewer)**: 
  - Validates diagnosis against source material
  - Assigns confidence scores (0-100%) based on strict adherence
  - Provides clinical critique and identifies potential hallucinations

### 3. **Hallucination Prevention**
- **Zero-Knowledge Policy**: LLM pretends to have no prior medical knowledge
- **Exclusion Rule**: LLM cannot mention diseases not explicitly in guidelines
- **Strict Auditing**: Every claim is validated against source documents
- **Confidence Scoring**: Systematic evaluation of diagnostic reliability

### 4. **User-Friendly Interface**
- Built with Streamlit for interactive web-based usage
- Real-time diagnostic results with color-coded confidence indicators
- Collapsible source reference section for transparency
- Patient profile capture (age, sex, medical history, symptoms)

---

## 🏗️ System Architecture

### **Project Structure**
```
pharm/
├── app.py                      # Main Streamlit application
├── ingest_data.py             # Data ingestion pipeline
├── requirements.txt           # Python dependencies
├── statpearls_chroma_db/      # Vector database (ChromaDB)
└── README.md                  # This file
```

### **Data Flow**

```
Patient Input
    ↓
[Symptom-Based Retrieval]
    ↓ (ChromaDB Similarity Search)
Clinical Guidelines (5 best matches)
    ↓
[Agent A: Diagnosis Generator]
    ↓ (Groq LLM - llama-3.3-70b)
Differential Diagnosis Draft
    ↓
[Agent B: Confidence Auditor] ← [Agent B: Peer Reviewer]
    ↓ (Groq LLM) ↓ (Groq LLM)
Confidence Score + Critique
    ↓
[UI Visualization]
```

---

## 🔧 Core Components

### **app.py** - Main Application
A Streamlit-based interactive diagnostic engine with three main functions:

#### `generate_diagnosis(patient_profile, context)`
- **Input**: Patient profile (age, sex, history, symptoms) + Retrieved clinical guidelines
- **Process**: LLM generates differential diagnosis based strictly on guidelines
- **Output**: Markdown-formatted diagnosis with inline citations
- **Key Constraint**: Zero prior knowledge - only uses provided guidelines

#### `generate_confidence_score(draft_diagnosis, context, patient_profile)`
- **Input**: Draft diagnosis + Guidelines + Patient profile
- **Process**: LLM audits diagnosis for hallucinations and adherence to guidelines
- **Output**: JSON with confidence score (0-100%)
- **Scoring Logic**:
  - ✅ Patient facts (travel, age, symptoms) do NOT lower score
  - ❌ Made-up diseases/treatments lower score
  - ❌ Unsupported clinical correlations lower score

#### `generate_peer_review(draft_diagnosis, context, patient_profile)`
- **Input**: Same as confidence scorer
- **Process**: Clinical peer reviewer critiques the diagnosis
- **Output**: 3-4 sentence paragraph identifying weaknesses
- **Focus**: Real clinical hallucinations, not patient facts

#### `retrieve_clinical_context(db, symptoms, k=5)`
- **Input**: Patient symptoms + Database
- **Process**: Semantic similarity search in ChromaDB
- **Output**: Top 5 most relevant clinical documents with metadata
- **Search Method**: HuggingFace embeddings (all-MiniLM-L6-v2)

---

### **ingest_data.py** - Data Pipeline
Automated web scraping and vector database ingestion system.

#### Data Sources
- **50 Direct Clinical Links**: Pre-selected StatPearls articles covering:
  - Respiratory: Tuberculosis, Pneumonia, Asthma, COPD, PE, Pneumothorax
  - Cardiac: Heart Failure, MI, AFib, Stroke, Endocarditis, Pericarditis
  - Metabolic: Diabetes, Hypercalcemia, Thyroid disorders
  - GI: Pancreatitis, Appendicitis, Peptic ulcer, IBD
  - Infectious: Sepsis, Meningitis, Hepatitis
  - Neurological: MS, Parkinson's, Alzheimer's, Epilepsy
  - Renal: AKI, CKD, Pyelonephritis
  - And many more...

#### `scrape_article(url, expected_title)`
- **Process**: 
  1. Fetches HTML from StatPearls article
  2. Extracts clinical sections: Introduction, Etiology, Epidemiology, Pathophysiology, History & Physical, Evaluation, Treatment, Differential Diagnosis
  3. Cleans HTML (removes navigation, TOC, formatting)
  4. Returns structured text with metadata
- **Error Handling**: Graceful failures for rate-limited or inaccessible articles
- **Rate Limiting**: 2-5 second delays between requests to avoid IP bans

#### `main()`
- Initializes HuggingFace embeddings
- Processes all 50 articles sequentially
- Splits text into chunks (1000 chars, 150 overlap)
- Stores chunks in ChromaDB with source metadata
- Tracks success/failure and execution time

---

## 📋 Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI Framework** | Streamlit | Interactive web interface |
| **LLM Provider** | Groq API | Fast inference with Llama 3.3-70B |
| **Vector Database** | ChromaDB | Semantic search & document storage |
| **Embeddings** | HuggingFace (all-MiniLM-L6-v2) | Text vectorization |
| **Web Scraping** | BeautifulSoup 4 | HTML parsing |
| **Text Chunking** | LangChain | Document splitting for indexing |
| **Language** | Python 3.8+ | Core implementation |

---

## 🚀 Installation & Setup

### **1. Clone the Repository**
```bash
git clone https://github.com/vijay-kamat/medbot.git
cd medbot
```

### **2. Create Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # macOS/Linux
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Configure API Keys**
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get your Groq API key from: https://console.groq.com

### **5. Build the Clinical Database**
```bash
python ingest_data.py
```

This will:
- Scrape 50 clinical articles from StatPearls
- Create vector embeddings
- Populate ChromaDB (takes ~10-15 minutes)

### **6. Run the Application**
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📖 Usage Guide

### **Step 1: Enter Patient Profile**
In the sidebar, provide:
- **Age**: Patient age (1-120)
- **Sex**: Male/Female/Other
- **Medical History**: Relevant background (e.g., "Recent travel to Southeast Asia")
- **Presenting Symptoms**: Detailed symptom description

### **Step 2: Run Diagnostics**
Click "🚀 Run Diagnostics" button

### **Step 3: Interpret Results**

**Left Panel - Primary Diagnosis (Agent A)**
- Differential diagnosis based on clinical guidelines
- Expandable "View Retrieved Source Chunks" to see evidence
- Shows which StatPearls articles support the diagnosis

**Right Panel - Verification Audit (Agent B)**
- **Confidence Score** (color-coded):
  - 🟢 **90-100%**: Highly supported, strict adherence
  - 🟡 **60-89%**: Acceptable, minor violations
  - 🔴 **<60%**: Unreliable, significant hallucinations
- **Auditor Peer-Review**: Specific critique of diagnosis quality

---

## 🔐 Safety Features

### **Anti-Hallucination Mechanisms**
1. **Strict Source Attribution**: LLM can only use provided guidelines
2. **Dual-Agent Validation**: Independent auditor checks diagnosis
3. **Patient vs. Clinical Hallucinations**: Distinguishes between
   - ✅ Patient facts (travel, symptoms, age) - legitimate context
   - ❌ Invented diseases/treatments - actual hallucinations
4. **Confidence Scoring**: Transparent reliability metric
5. **Source Transparency**: All evidence is traceable to origin articles

### **Limitations**
- **Not a replacement for clinical judgment**: For educational/research use
- **Limited to indexed articles**: Cannot reference diseases outside StatPearls database
- **Static knowledge**: Updated only when ingest_data.py is re-run
- **LLM limitations**: May still hallucinate despite safeguards (that's why auditor is needed)

---

## 📊 Example Usage

**Input:**
- Age: 45
- Sex: Male
- History: Recent extended travel to Southeast Asia for 3 months
- Symptoms: Persistent productive cough for 4 weeks, hemoptysis, night sweats, 10-pound weight loss

**Output:**
```
Differential Diagnosis (Agent A):
- Tuberculosis (most likely, supported by travel history + symptoms)
- Pneumonia (possible, but less likely given chronic presentation)
- Lung Cancer (low probability without smoking history)

Confidence Score: 92% 🟢
(Highly Supported - Diagnosis strictly adheres to TB and pneumonia guidelines)

Peer Review:
"The diagnosis appropriately prioritizes tuberculosis given the epidemiological risk 
factors (SE Asia travel) and classic presentations (hemoptysis, night sweats, weight loss). 
Inclusion of pneumonia and malignancy is appropriate for differential completeness."
```

---

## 🔄 Workflow for Extending the Database

To add more clinical articles:

1. **Edit `ingest_data.py`**: Add articles to `DIRECT_LINKS` list
   ```python
   {"title": "New Disease", "url": "https://www.ncbi.nlm.nih.gov/books/NBK..."},
   ```

2. **Run ingestion**: 
   ```bash
   python ingest_data.py
   ```

3. **Verify in app**: New disease will be searchable

---

## 🛠️ Troubleshooting

### **Error: "Could not load ChromaDB"**
- Run `python ingest_data.py` to create the database

### **Error: "GROQ_API_KEY not found"**
- Ensure `.env` file exists with valid Groq API key

### **Slow startup**
- First load caches embeddings model (~500MB download)
- Subsequent runs are faster

### **Getting generic diagnoses**
- Check that symptoms are specific enough
- Verify database was successfully created with `python ingest_data.py`

---

## 📚 References

- **StatPearls**: https://www.ncbi.nlm.nih.gov/books/
- **Groq API**: https://console.groq.com/
- **ChromaDB**: https://www.trychroma.com/
- **Streamlit**: https://streamlit.io/
- **LangChain**: https://python.langchain.com/

---

## 📝 License

This project is for educational and research purposes only.

---

## 🤝 Contributing

Pull requests welcome! Focus areas:
- Adding more clinical articles
- Improving hallucination detection
- Enhanced UI/UX
- Performance optimization

---

## ⚠️ Medical Disclaimer

**This system is NOT a medical device and should NOT be used for clinical decision-making without physician oversight.** It is designed for educational purposes and research applications. Always consult qualified healthcare professionals for actual patient care.

---

## 👨‍💻 Author

**Vijay Kamat**  
GitHub: [@vijay-kamat](https://github.com/vijay-kamat)

---

## 📞 Support

For issues or questions, open an issue on the GitHub repository.

---

**Last Updated**: May 2026
