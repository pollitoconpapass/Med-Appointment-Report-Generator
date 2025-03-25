import os
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


txt_count = 0
def generate_txt_from_text(text):
    global txt_count

    txt_count += 1
    txt_route = f"../docs/summary_{txt_count}.txt"
    with open(txt_route, "w") as f:
        f.write(text)

    return txt_route

    

def generate_pdf_from_txt(input_file):
    pdf_count = random.randint(3000, 10000)

    pdf = FPDF()
    with open(input_file, 'r') as f:
        text = f.read()

    pdf.add_page()
    pdf.set_font('Arial', size=12)

    pdf.multi_cell(0, 10, txt=text, align='L')
    pdf_path = f'../docs/summary_{pdf_count}.pdf'

    pdf.output(pdf_path)
    return pdf_path


def med_sumy(dialogue):
    summary = generate_summary(dialogue)
    txt_route = generate_txt_from_text(summary)
    pdf_path = generate_pdf_from_txt(txt_route)

    os.remove(txt_route)
    return pdf_path
