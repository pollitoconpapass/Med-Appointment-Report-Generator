import os, io
import tiktoken
from fpdf import FPDF
from typing import List
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


# Initialize Azure OpenAI client
azure_endpoint = os.getenv("AZURE_ENDPOINT")
api_key = os.getenv("AZURE_API_KEY")
api_version = os.getenv("AZURE_API_VERSION")

client = AzureOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=azure_endpoint
)

# Other configurations
chunk_size = 3000
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
conversation_summary_prompt = (
    "You are a highly skilled medical transcriptionist. Your task is to generate a concise and accurate medical report "
    "from the provided conversation between a doctor and a patient. The summary should include the following key information: "
    "patient's symptoms, doctor's diagnoses, prescribed treatments, and any follow-up instructions. "
    "Ensure the summary is written in a professional and formal tone, suitable for inclusion in a medical report. "
    "Use bullet points for clarity where appropriate."
)

summarize_summaries_prompt = (
    "Here are some summaries of a conversation between a doctor and a patient. "
    "Please summarize the summaries into a concise and accurate medical report. "
    "The report should include the following key information: patient's symptoms, doctor's diagnoses, prescribed treatments, "
    "and any follow-up instructions. Ensure the summary is written in a professional and formal tone, suitable for inclusion in a medical report. "
    "Use bullet points for clarity where appropriate."
)

# === LLM INITALIZATION ===
def llm_query(prompt, dialogue: str)-> str:
    try:
        response = client.chat.completions.create(
            model="gpt4-o",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": dialogue},
            ]
        )

        return response.choices[0].message.content
    
    except Exception as e:
        raise Exception(f"Error in LLM query: {e}")

# === COUNTING TOKENS TO VERIFY DIALOGUE LENGTH ===
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# === SPLITTING TEXT IN CASE THE DIALOGUE IS TOO LONG ===
def split_text(text: str) -> List[str]:
    chunks = []
    current_chunk = []
    current_length = 0
    
    sentences = text.split('. ')
    
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        
        if current_length + sentence_tokens > chunk_size:
            chunks.append('. '.join(current_chunk) + '.')
            current_chunk = [sentence]
            current_length = sentence_tokens
        else:
            current_chunk.append(sentence)
            current_length += sentence_tokens
    
    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')
    
    return chunks

# === GENERATING SUMMARY (recursive function) ===
def generate_summary(dialogue):
    if count_tokens(dialogue) <= chunk_size:
        return llm_query(conversation_summary_prompt, dialogue)
    
    chunks = split_text(dialogue)
    summaries = []

    for chunk in chunks:
        summary = llm_query(conversation_summary_prompt, chunk)
        summaries.append(summary)

    combined_summary = " ".join(summaries)
    if count_tokens(combined_summary) > chunk_size:
        return generate_summary(combined_summary)
         
    return llm_query(summarize_summaries_prompt, combined_summary)


# === GENERATING PDF FROM THE RESULTANT SUMMARY ===
def generate_pdf_from_text(text):
    if not text:
        raise ValueError("Text cannot be empty.")
    
    try: 
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', size=12)
        pdf.multi_cell(0, 10, txt=text, align='L')
        
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)
        
        return pdf_buffer
    
    except Exception as e:
        raise Exception(f"Error generating PDF: {str(e)}")

# === MAIN SUMMARIZER FUNCTION ===
def med_sumy(dialogue):
    summary = generate_summary(dialogue)
    pdf_buffer = generate_pdf_from_text(summary)

    return pdf_buffer, summary