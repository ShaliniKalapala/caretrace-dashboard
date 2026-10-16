# CareTrace AI — Public Dashboard Starter

A Streamlit dashboard for the DATATHON “Health — The Forgotten Patient” synthetic dataset.

## Files
- `app.py` — dashboard
- `patients.csv`
- `encounters.csv`
- `departments.csv`
- `diagnostic_tests.csv`
- `requirements.txt` — Python dependencies

## Run locally for testing
```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Local testing is optional before deployment, but recommended to catch issues.

## Deploy publicly
1. Create a GitHub account or sign in.
2. Create a **public** repository named `caretrace-ai-dashboard`.
3. Upload all six files in this folder to the repository root.
4. Visit https://share.streamlit.io/ and connect GitHub.
5. Click **Create app** and select the repository, branch `main`, and `app.py`.
6. Optionally set the app URL to a memorable available name.
7. Click **Deploy** and wait for the build to finish.
8. Open the generated `https://....streamlit.app` URL in an incognito/private browser window to verify public access.
9. Share that URL with the DATATHON judges.

## Dataset safety
The provided README identifies these files as synthetic educational data. Keep that limitation visible in the dashboard and presentation. Do not upload real patient data or secrets to a public repository.

## Notes
This starter implements descriptive analytics and rule-based review flags. It does **not** yet include a trained ML prediction model. Do not describe the rule-based flags as ML predictions.
