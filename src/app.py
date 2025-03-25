import time
import random
import requests
import streamlit as st
from dialogue_sumy import med_sumy


st.title("Med Appointment Report Generator 🩺💊")


# === USER INPUT ===
language_dict = {
    "Spanish": "es",
    "English USA": "en_us",
    "English UK": "en_uk"
}

option_lang = st.selectbox(
    "What language would you like to transcribe?",
    ("Spanish", "English USA", "English UK"))

option_speakers = st.selectbox(
    "How many speakers are there?",
    (1, 2, 3, 4, 5))

file_uploader = st.file_uploader("Select an audio file", type=["wav", "mp3"])


# === INTERPRETING VALUES ===
language_code = language_dict.get(option_lang, "en_us")
num_speakers = option_speakers


# === REQUEST TO ASSEMBLYAI ENDPOINT ===
if file_uploader:
    start = time.time()

    with st.spinner('Loading...'):
        url = f"http://localhost:8000/transcribe?language_code={language_code}&num_speakers={num_speakers}"
        files = {"file": file_uploader}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        # SPEAKER DIARIZATION
        transcription_results = response.json()["transcription"]
        

        conversation = " "
        for result in transcription_results:
            whole_text = f"Speaker {result['speaker']}: {result['text']}"
            conversation += whole_text + "\n"

        st.success("Transcription successful!")
            

        # SUMMARY
        with st.spinner('Creating the Summary PDF...'):
            pdf_buffer, summary = med_sumy(conversation)
            num = random.randint(3000, 10000)

            st.success("Summary created!")
            st.write(f"Time taken: {time.time() - start} seconds")

            st.text_area("Summary", summary, height=300)

            st.download_button(
                label="Download Summary as PDF",
                data=pdf_buffer,
                file_name=f"summary_{num}.pdf",
                mime="application/pdf"
            )
            
    else:
        st.write("Error:", response.text)
