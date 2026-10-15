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
- Statistical analysis: SciPy
- Visualization: Chart.js
- Dataset format: CSV
- Database: none
- Hosting: localhost

## Project structure

```text
MDM/
├── app.py
├── statistics_engine.py
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
├── docs/
│   └── dataset_notes.md
└── tests/
    ├── __init__.py
    ├── test_api.py
    └── test_statistics.py
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

## Current functionality

- Responsive six-screen dashboard with desktop, tablet, and mobile layouts
- Live backend connection indicator powered by `GET /api/health`
- Basic JSON error responses for unknown API routes and server errors
- Original research CSV preserved in `data/`
- CSV upload and verified default-dataset preview
- File, size, source, column, empty-data, text-content, and numeric/ordinal validation
- Mean, median, sample standard deviation, Spearman correlation, simple linear
  regression, and two-sided Spearman hypothesis testing
- Missing-pair and duplicate-row reporting without silent substitution or removal
- Graph-ready scatter, regression-line, and frequency data
- Default-dataset and drag-and-drop CSV workflows with live previews
- Dynamic X/Y variable selection based on the active dataset
- Real result cards, scatter/regression plots, distribution charts, findings,
  and a report-ready summary generated from API responses
- Copy-to-clipboard findings and an explicitly deferred Phase 4 PDF control
- Automated mathematical and Flask API tests

The browser keeps an uploaded `File` object only in page memory. The backend
processes uploads in memory and does not retain them.

## API endpoints

### `GET /api/health`

Returns the backend status.

### `POST /api/preview`

Send `multipart/form-data` with either:

- `file`: a CSV upload no larger than 5 MB, or
- `source=default`: the verified research CSV included in `data/`.

The response includes dimensions, columns, inferred types, missing values,
duplicates, five actual preview records, and suggested analysis columns.

### `POST /api/analyze`

Send the same dataset source plus:

- `connectivity_column`: exact CSV column name for the predictor
- `learning_column`: exact CSV column name for the outcome

The response contains dataset metadata, processing details, valid-pair counts,
descriptive statistics, Spearman correlation, linear regression, hypothesis-test
results, visualization-ready values, and warnings. If correlation is valid but
regression cannot be calculated defensibly, the regression object keeps the same
keys with `status: "unavailable"`, null results, and an explanatory reason.
Uploaded files are processed in memory and are not retained.

Example using the included dataset:

```powershell
$form = @{
    source = "default"
    connectivity_column = "Internet facility in your locality"
    learning_column = "Your interaction in online mode"
}
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5000/api/analyze" -Form $form
```

Only numeric columns and two documented ordered text scales are accepted. The
accepted text scales are `Bad < Average < Good` and
`Very Bad < Bad < Average < Good < Very Good`. A partial scale containing only
overlapping labels such as `Bad` and `Good` is rejected as ambiguous. Unordered
categories and files containing null bytes are also rejected.

## Run the tests

```powershell
python -m unittest discover -s tests -v
```

## Planned phases

- **Phase 3:** Complete — dashboard, CSV workflow, analysis controls, findings,
  report view, and Chart.js visuals
- **Phase 4:** Integration hardening, mathematical verification, PDF export,
  and bug fixes
- **Phase 5:** Academic report based on verified application outputs
