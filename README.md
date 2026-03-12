# Medical Appointment Report Generator (MARGe) 🩺💊

A web application that transcribes medical appointments and generates summarized medical reports using AI technology.

## Configuration

Add the respective API keys in the `.env` file in the root directory following the example of `.env.example`.

Inside the `ui` folder create another `.env` following the example of the `ui/.env.example`.

### Backend

To run the backend open a terminal and run:

```sh
cd server
pip install -r requirements.txt
uvicorn app:app --reload
```

### Frontend

To run the frontend open another terminal and run:

```sh
cd ui
npm i
npm start
```
