# Kinetic Coach — AI Avatar Product MVP

Kinetic Coach is a focused AI-avatar wellness MVP for people who want a simple,
realistic way to build daily movement habits.

## What the MVP does

1. 60-second movement check-in
2. Calculates a transparent readiness snapshot
3. Creates a 10-minute starter plan
4. Provides an animated AI avatar
5. Lets the user chat with the AI coach
6. Uses browser text-to-speech when the user presses "Speak"
7. Collects lightweight validation feedback
8. Logs product events locally for MVP analytics

## Product hypothesis

A conversational AI avatar can make personalized movement guidance feel more
human, understandable and actionable than a static questionnaire/result screen.

## Tech stack

- Python
- Streamlit
- OpenAI Responses API
- SQLite
- HTML/CSS/JavaScript avatar component

## Run locally

### 1. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the API key

Copy:

```text
.streamlit/secrets.toml.example
```

to:

```text
.streamlit/secrets.toml
```

Then put your API key in it.

Never commit the secrets file.

### 4. Run

```bash
streamlit run app.py
```

## Demo mode

If no API key is configured, the app still loads and the assessment works.
The chat will show a demo-mode message instead of making an API call.

## Deployment

The easiest path is Streamlit Community Cloud:

1. Create a GitHub repository.
2. Upload the project files.
3. Open Streamlit Community Cloud.
4. Select the repository and `app.py`.
5. Add `OPENAI_API_KEY` and `OPENAI_MODEL` in the app Secrets settings.
6. Deploy.

## Validation

Do not invent traction numbers.

Share the live app with real testers and record:
- sessions
- assessments completed
- avatar chats
- feedback submissions
- willingness to return
- qualitative comments

The final internship deck should report observed numbers only.

## Safety

The product is positioned as general wellness/habit support.
It does not diagnose medical conditions and should not be presented as a medical tool.
Users should stop exercise and seek appropriate professional care for concerning symptoms.
