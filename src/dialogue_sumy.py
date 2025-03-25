import os, io
import random
from fpdf import FPDF
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


def generate_summary(dialogue):
    response = client.chat.completions.create(
        model="gpt4-o",
        messages=[
            {"role": "system", "content": (
                "You are a highly skilled medical transcriptionist. Your task is to generate a concise and accurate medical report "
                "from the provided conversation between a doctor and a patient. The summary should include the following key information: "
                "patient's symptoms, doctor's diagnoses, prescribed treatments, and any follow-up instructions. "
                "Ensure the summary is written in a professional and formal tone, suitable for inclusion in a medical report. "
                "Use bullet points for clarity where appropriate."
            )},
            {"role": "user", "content": dialogue},
        ]
    )

    return response.choices[0].message.content
    

def generate_pdf_from_text(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', size=12)
    pdf.multi_cell(0, 10, txt=text, align='L')
    
    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    
    return pdf_buffer


def med_sumy(dialogue):
    summary = generate_summary(dialogue)
    pdf_buffer = generate_pdf_from_text(summary)

    return pdf_buffer, summary