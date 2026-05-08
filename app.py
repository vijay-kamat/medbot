import os
import json
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- CONFIGURATION ---
load_dotenv()
DB_DIR = "./statpearls_chroma_db"

# --- PAGE SETUP ---
st.set_page_config(page_title="CIS | Diagnostic Engine", page_icon="🩺", layout="wide")

# Cache the database loading so it doesn't reload on every button click
@st.cache_resource
def load_database():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
    return db

def retrieve_clinical_context(db, symptoms, k=5):
    results = db.similarity_search(symptoms, k=k)
    context_string = ""
    for i, res in enumerate(results):
        context_string += f"\n--- [Source {i+1}] ---\n"
        context_string += f"Title: {res.metadata['title']}\n"
        context_string += f"URL: {res.metadata['source']}\n"
        context_string += f"Text: {res.page_content}\n"
    return context_string, results

# --- AGENT FUNCTIONS ---
def generate_diagnosis(patient_profile, context):
    client = Groq()
    system_prompt = """
You are a strict Medical Search and Retrieval Agent. Your only function is to summarize the 'Retrieved Clinical Guidelines' in relation to a patient profile.
1. **Zero-Knowledge Policy**: You must pretend you have NO prior medical knowledge.
2. **Exclusion Rule**: If a disease is NOT explicitly described in the provided guidelines, you are FORBIDDEN from mentioning it.
3. **Hyperlinked Citations**: Every clinical claim you make MUST be cited using a Markdown link (e.g., [Source 1](URL)).
"""
    user_prompt = f"### PATIENT PROFILE\n{patient_profile}\n\n### RETRIEVED GUIDELINES\n{context}\n\nProvide the Differential Diagnosis with hyperlinked citations."
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.2
    )
    return response.choices[0].message.content

def generate_confidence_score(draft_diagnosis, context, patient_profile):
    client = Groq()
    scorer_prompt = """
You are a strict Data Auditor. Assign a 'confidence_score' (0-100) based on strict adherence of the Draft to the Guidelines. 

CRITICAL RULE: The drafter is allowed to mention facts from the PATIENT PROFILE (e.g., travel history, age, specific symptoms). Do NOT penalize the drafter or lower the score for mentioning patient facts. Only penalize if they invent diseases, treatments, or clinical correlations NOT found in the Guidelines.

Respond ONLY with JSON: {"confidence_score": 85}
"""
    payload = f"### PATIENT PROFILE\n{patient_profile}\n\n### GUIDELINES\n{context}\n\n### DRAFT DIAGNOSIS\n{draft_diagnosis}"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[{"role": "system", "content": scorer_prompt}, {"role": "user", "content": payload}], 
        temperature=0.0, 
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def generate_peer_review(draft_diagnosis, context, patient_profile):
    client = Groq()
    reviewer_prompt = """
You are a Clinical Peer Reviewer. Write a concise, 3-4 sentence paragraph critiquing the draft against the guidelines. 

CRITICAL RULE: The drafter is analyzing a specific PATIENT PROFILE. Do NOT flag the patient's personal history, travel, or reported symptoms as hallucinations. Only flag clinical hallucinations (e.g., mentioning outside diseases or treatments not found in the text).

Do not write a score. Just write the critique.
"""
    payload = f"### PATIENT PROFILE\n{patient_profile}\n\n### GUIDELINES\n{context}\n\n### DRAFT DIAGNOSIS\n{draft_diagnosis}"
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[{"role": "system", "content": reviewer_prompt}, {"role": "user", "content": payload}], 
        temperature=0.2
    )
    return response.choices[0].message.content

# --- UI LAYOUT ---
st.title("🩺 Clinical Intelligence System")
st.markdown("**Multi-Agent Diagnostic Retrieval Engine**")
st.divider()

# Load DB silently
try:
    db = load_database()
except Exception as e:
    st.error("Could not load ChromaDB. Ensure you have run ingest_data.py first.")
    st.stop()

# Sidebar for Input
with st.sidebar:
    st.header("📋 Patient Profile")
    age = st.number_input("Age", min_value=1, max_value=120, value=45)
    sex = st.selectbox("Sex", ["Male", "Female", "Other"])
    history = st.text_area("Medical History", value="Recent extended travel to Southeast Asia for 3 months. No prior chronic conditions. Non-smoker.")
    symptoms = st.text_area("Presenting Symptoms", value="Persistent productive cough for 4 weeks, recently coughing up blood-tinged sputum (hemoptysis). He reports drenching night sweats, fatigue, and an unintentional 10-pound weight loss.", height=150)
    
    run_btn = st.button("🚀 Run Diagnostics", type="primary", use_container_width=True)

# Main Execution Logic
if run_btn:
    patient_profile = {"age": age, "sex": sex, "history": history, "symptoms": symptoms}
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.subheader("📝 Primary Diagnosis (Agent A)")
        with st.spinner("Retrieving clinical guidelines & drafting diagnosis..."):
            context, raw_results = retrieve_clinical_context(db, symptoms)
            diagnosis = generate_diagnosis(patient_profile, context)
            st.markdown(diagnosis)
            
            with st.expander("📚 View Retrieved Source Chunks"):
                for doc in raw_results:
                    st.markdown(f"**[{doc.metadata['title']}]({doc.metadata['source']})**")
                    st.caption(doc.page_content[:300] + "...")

    with col2:
        st.subheader("🛡️ Verification Audit (Agent B)")
        with st.spinner("Running NLI Math & Peer Review..."):
            # Get Score
            raw_score_json = generate_confidence_score(diagnosis, context)
            try:
                score = json.loads(raw_score_json).get("confidence_score", 0)
            except:
                score = 0
            
            # Get Review
            critique = generate_peer_review(diagnosis, context)
            
            # Display Score visually
            if score >= 90:
                st.success(f"### 🟢 Confidence Score: {score}%\n*(Highly Supported & Strict)*")
            elif score >= 60:
                st.warning(f"### 🟡 Confidence Score: {score}%\n*(Contains Rule Violations or Speculation)*")
            else:
                st.error(f"### 🔴 Confidence Score: {score}%\n*(Unsafe / Hallucinated)*")
            
            st.markdown("👨‍⚕️ **Auditor Peer-Review:**")
            st.info(critique)