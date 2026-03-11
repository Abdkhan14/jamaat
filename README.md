# Jamaat

A full-stack web app that aggregates daily prayer times from mosques in Scarborough, ON. It scrapes each mosque's website using Playwright, extracts structured prayer times via an OpenAI LLM, and serves them through a REST API to a React frontend.

## Features

- Automatically scrapes prayer times from multiple mosque websites every 24 hours
- Uses GPT to parse and extract prayer times (Fajr, Zuhr, Asr, Maghrib, Isha, Jummah) from raw web text
- Normalizes and validates extracted times (adhan vs. iqamah, time ordering, Jummah slots)
- Persists prayer times to a database and serves them via a Flask API
- React frontend displays prayer times per mosque with real-time clock awareness

## Mosques Covered

| Mosque | Address |
|---|---|
| Baitul Aman | 3114 Danforth Ave, Scarborough, ON |
| Baitul Mukarram | 3340 Danforth Ave, Scarborough, ON |
| Masjid Al-Abedeen | 1 Stamford Square N, Scarborough, ON |
| The Sunatul Jamaat | 347 Danforth Rd, Scarborough, ON |

## Tech Stack

**Backend** — Python, Flask, Flask-SQLAlchemy, Playwright, APScheduler, OpenAI API

**Frontend** — React 19, TypeScript, Vite, MUI, TanStack Query, styled-components

## Project Structure

```
jamaat/
├── backend/
│   ├── app.py          # Flask app, scraping logic, LLM extraction, scheduler
│   ├── mosques.py      # Mosque registry (name, address, website, coordinates)
│   ├── config.py       # App configuration
│   ├── models/
│   │   └── prayerTimes.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   ├── prayerTimes.tsx
    │   ├── components/
    │   ├── hooks/
    │   └── types.tsx
    └── package.json
```

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

Create a `.env` file:

```
OPENAI_API_KEY=your_key_here
```

Run the server:

```bash
python app.py
```

The API will be available at `http://localhost:5000`. Prayer times are refreshed every 24 hours automatically.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

## API

`GET /prayer-times` — Returns prayer times for all mosques, merged with mosque metadata (name, address, coordinates).
