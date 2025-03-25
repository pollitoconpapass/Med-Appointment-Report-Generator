# Medical Appointment Report Generator (MARGe) 🩺💊

A web application that transcribes medical appointments audio files and generates summarized medical reports using AI technology.

## Features

- Audio transcription support for multiple languages:
  - Spanish
  - US English 
  - UK English
- Speaker diarization (supports 1-5 speakers)
- Medical report generation with GPT-4
- PDF report download
- Real-time processing status
- Simple web interface built with Streamlit

## Prerequisites

- Python 3.11+
- AssemblyAI API key
- Azure OpenAI API key

## Installation

1. Clone this repository
2. Install dependencies:
```sh
pip install -r requirements.txt
```
3. Configure environment variables in `.env`:
```
ASSEMBLY_AI_API_KEY=your_assemblyai_key
AZURE_ENDPOINT=your_azure_endpoint
AZURE_API_KEY=your_azure_key
AZURE_API_VERSION=your_api_version
```

## Usage

1. Start the FastAPI backend:
```sh
cd src
python endpoint.py
```

2. In a new terminal, start the Streamlit frontend:
```sh
cd src
streamlit run app.py
```

3. Open your browser and navigate to http://localhost:8501

4. Upload an audio file (.wav or .mp3), select the language and number of speakers

5. Wait for processing and download your summarized medical report as PDF

## Project Structure

```
.
├── docs/                   # Generated PDF summaries (examples in Spanish)
├── src/
    |── test/               # Test scripts
│   ├── app.py              # Streamlit frontend
│   ├── dialogue_sumy.py    # Summary generation 
│   └── endpoint.py         # FastAPI backend
│   
└── requirements.txt        # Project dependencies
```

## Technologies Used

- [Streamlit](https://streamlit.io/) - Frontend framework
- [FastAPI](https://fastapi.tiangolo.com/) - Backend API
- [AssemblyAI](https://www.assemblyai.com/) - Speech-to-text / Speaker diarization
- [Azure OpenAI](https://azure.microsoft.com/products/ai-services/openai-service) - Report generation
- [FPDF](http://www.fpdf.org/) - PDF generation
