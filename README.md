# Internet Speed and Online Learning Experience

A lightweight academic web application that investigates whether students'
reported internet facilities are associated with their online learning
experience, interaction, performance, and satisfaction.

## Problem statement

Internet connectivity varies across users and locations. This project examines
whether connectivity quality is associated with differences in online learning
experience and class participation. The source survey contains an ordinal
internet-facility rating; it does **not** contain measured internet speed in
Mbps or a network-interruption frequency field.

## Technology stack

- Frontend: HTML5, CSS3, and vanilla JavaScript
- Backend: Python 3.11+ and Flask
- Data processing: Pandas and NumPy
- Statistical analysis: SciPy (planned for Phase 2)
- Visualization: Chart.js (planned for Phase 3)
- Dataset format: CSV
- Database: none
- Hosting: localhost

## Project structure

```text
MDM/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   └── app.js
├── data/
│   ├── .gitkeep
│   └── ONLINE EDUCATION SYSTEM REVIEW.csv
└── docs/
    └── dataset_notes.md
```

## Local setup

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the development server:

```powershell
python app.py
```

Open <http://127.0.0.1:5000> in a browser. The health endpoint is available at
<http://127.0.0.1:5000/api/health>.

Alternatively, use Flask's development command:

```powershell
flask --app app run --debug
```

## Phase 1 functionality

- Responsive academic landing page
- Live backend connection indicator powered by `GET /api/health`
- Basic JSON error responses for unknown API routes and server errors
- Original research CSV preserved in `data/`
- Verified dataset schema and preparation notes
- Startup does not depend on loading or processing the dataset

The dataset, analysis, and visualization areas are intentionally informational
in Phase 1. They do not present nonfunctional controls as usable features.

## Planned phases

- **Phase 2:** Data validation, statistical calculations, and analysis APIs
- **Phase 3:** CSV upload, dashboard interactions, results, and Chart.js visuals
- **Phase 4:** Integration, mathematical verification, and bug fixes
- **Phase 5:** Academic report based on verified application outputs
