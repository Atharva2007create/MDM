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
- Statistical analysis: NumPy and Pandas
- Visualization: locally vendored Chart.js 4.5.1
- PDF generation: ReportLab
- Dataset format: CSV
- Database: none
- Hosting: localhost

## Project structure

```text
MDM/
├── app.py
├── statistics_engine.py
├── pdf_report.py
├── requirements.txt
├── README.md
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   ├── style.css
│   ├── app.js
│   ├── favicon.svg
│   └── vendor/chartjs/
│       ├── chart.umd.min.js
│       └── LICENSE.md
├── data/
│   ├── .gitkeep
│   └── ONLINE EDUCATION SYSTEM REVIEW.csv
├── samples/
│   ├── 01_strong_positive_connectivity.csv
│   ├── 02_network_interruptions.csv
│   ├── 03_rural_mobile_learning.csv
│   ├── 04_mixed_learning_factors.csv
│   └── 05_missing_values_practice.csv
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
- Copy-to-clipboard findings and genuine in-memory PDF report downloads
- Automatic invalidation of old results when the dataset or selected variables change
- Offline chart rendering through the pinned local Chart.js 4.5.1 UMD build
- Automated mathematical and Flask API tests

The browser keeps an uploaded `File` object only in page memory. The backend
processes uploads in memory and does not retain them.

Chart.js is served from `static/vendor/chartjs/`, so chart rendering does not
require an internet connection. The bundled library remains licensed under its
included MIT license.

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

### `POST /api/report/pdf`

Uses the same multipart fields as `/api/analyze`. The backend reloads and
validates the selected dataset, repeats the statistical analysis using the
shared engine, and returns `NetLearn_Analysis_Report.pdf` with content type
`application/pdf`. Statistical values supplied by the browser are never trusted.

## Usage

Live application: <https://netlearn-analytics.vercel.app>

1. Open the application and load the included dataset or upload a CSV.
2. Review the detected columns, preview rows, and data-quality summary.
3. Select a connectivity variable and a learning-outcome variable.
4. Run the analysis and review statistics and visualizations.
5. Open Findings or Report and download the generated PDF.

Five synthetic, upload-ready datasets are available in `samples/`. They cover
strong positive connectivity effects, network interruptions, rural mobile
learning, mixed learning factors, and missing-value handling.

The included dataset is **Online Education System - Review (2021)** by Sujatha
Radhakrishnan, DOI `10.17632/bzk9zbyvv7.1`. The verified local copy contains
1,033 rows and 23 columns with no missing values or exact duplicate rows. See
`docs/dataset_notes.md` for the complete schema, SHA-256, provenance, and
processing assumptions.

## Limitations

- Internet facility is a reported ordinal rating, not measured Mbps, latency,
  or interruption frequency.
- Statistical association does not establish causation.
- Spearman p-values can be less reliable for very small samples or extensive ties.
- Exploratory regression treats numerical rating levels as approximately equally spaced.
- The application is intended for ordinary small academic CSV datasets and can
  run locally or on its Vercel deployment.

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
- **Phase 4:** Complete — integration hardening, stale-state prevention,
  mathematical verification, real PDF export, and regression tests
- **Phase 5:** Academic report based on verified application outputs
