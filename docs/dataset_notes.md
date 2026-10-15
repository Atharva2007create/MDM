# Dataset notes

## Source and availability

- **Title:** Online Education System – Review
- **Publication date:** 26 December 2021
- **Version:** 1
- **Contributor:** Sujatha Radhakrishnan
- **DOI:** 10.17632/bzk9zbyvv7.1
- **Licence:** CC BY 4.0
- **Kaggle:** <https://www.kaggle.com/datasets/sujaradha/online-education-system-review>
- **Original research repository:** <https://data.mendeley.com/datasets/bzk9zbyvv7/1>
- **Availability:** Retrieved from the Mendeley Data public file endpoint without
  authentication on 16 October 2026.
- **Local original:** `data/ONLINE EDUCATION SYSTEM REVIEW.csv`
- **Published/local size:** 109,274 bytes
- **Published/local SHA-256:**
  `747852bcf1a7f3a7be8a2bccc56de224649627899a8f6daa853c7b6c0056e82c`

The matching hash confirms that the local CSV is unchanged from the downloaded
source file.

## Verified shape and data quality

- Rows: 1,033
- Columns: 23
- Missing values: 0 across all columns
- Exact duplicate rows: 0

These quality findings are used by the Phase 2 preview endpoint. Exact duplicate
rows are reported and retained; none are present in the original dataset.

## Actual schema

The types below are Pandas' inferred types when reading the original CSV with
default settings.

| Column | Inferred type | Distinct values | Missing |
|---|---:|---:|---:|
| `Gender` | string | 2 | 0 |
| `Home Location` | string | 2 | 0 |
| `Level of Education` | string | 3 | 0 |
| `Age(Years)` | integer | 24 | 0 |
| `Number of Subjects` | integer | 20 | 0 |
| `Device type used to attend classes` | string | 3 | 0 |
| `Economic status` | string | 3 | 0 |
| `Family size` | integer | 9 | 0 |
| `Internet facility in your locality` | integer | 5 | 0 |
| `Are you involved in any sports?` | string | 2 | 0 |
| `Do elderly people monitor you?` | string | 2 | 0 |
| `Study time (Hours)` | integer | 10 | 0 |
| `Sleep time (Hours)` | integer | 10 | 0 |
| `Time spent on social media (Hours)` | integer | 10 | 0 |
| `Interested in Gaming?` | string | 2 | 0 |
| `Have separate room for studying?` | string | 2 | 0 |
| `Engaged in group studies?` | string | 2 | 0 |
| `Average marks scored before pandemic in traditional classroom` | string | 10 | 0 |
| `Your interaction in online mode` | integer | 5 | 0 |
| `Clearing doubts with faculties in online mode` | integer | 5 | 0 |
| `Interested in?` | string | 3 | 0 |
| `Performance in online` | integer | 9 | 0 |
| `Your level of satisfaction in Online Education` | string | 3 | 0 |

## Potential analytical mappings

These mappings are candidates for later validation and analysis; they are not
statistical conclusions.

- **Connectivity variable:** `Internet facility in your locality` is a
  five-level reported rating described by the publisher as ranging from very
  bad to very good.
- **Learning-experience variables:** `Your interaction in online mode`,
  `Clearing doubts with faculties in online mode`, `Performance in online`, and
  `Your level of satisfaction in Online Education`.
- **Possible descriptive/context variables:** home location, education level,
  device type, economic status, study time, and availability of a separate
  study room.

## Verified values for primary candidate fields

- `Internet facility in your locality`: 1, 2, 3, 4, 5
- `Your interaction in online mode`: 1, 2, 3, 4, 5
- `Clearing doubts with faculties in online mode`: 1, 2, 3, 4, 5
- `Performance in online`: 2 through 10 (the value 1 is not present)
- `Your level of satisfaction in Online Education`: Average, Bad, Good
- `Average marks scored before pandemic in traditional classroom`: ten
  intervals from `0-10` through `91-100`

The publisher describes the five-level internet, interaction, and doubt-clearing
scales as ranging from very bad to very good. The CSV itself contains numerical
levels but no embedded codebook that explicitly maps each number to a label.

## Phase 2 processing rules and transformations

- The original CSV is read without modification. Uploaded CSVs are processed in
  memory and are not retained.
- Missing values are never replaced with zero. Rows missing either selected
  variable are excluded only from paired calculations, and the excluded count
  is returned.
- Exact duplicate rows are counted, reported, and retained.
- Numeric columns and numeric strings are converted with Pandas while preserving
  missing values.
- Positive and negative infinity are treated as invalid observations, converted
  to missing values in the analysis copy, counted, and excluded from paired
  calculations.
- Text values matching the complete documented order
  `Bad < Average < Good` are encoded as 1–3.
- Text values that include the five-level documented order
  `Very Bad < Bad < Average < Good < Very Good` are encoded as 1–5.
- Partial text scales containing only labels shared by both scales, such as
  `Bad` and `Good`, are rejected because their intended numerical spacing is
  ambiguous without an explicit codebook.
- Unordered text categories such as device type, gender, and location are not
  assigned arbitrary numbers and cannot be selected for these analyses.
- Uploaded files containing null bytes are rejected as non-text CSV input.
- Sample standard deviation uses `ddof=1`.
- Paired analyses require at least three valid observations and two non-constant
  selected variables.

## Statistical assumptions

- Spearman rank correlation is the primary association measure because it is
  suitable for ordered survey ratings and does not require a linear relationship.
- The two-sided Spearman significance test uses alpha = 0.05. A nonsignificant
  result is reported as “fail to reject H0,” never “accept H0.”
- The p-value is asymptotic and may be less reliable for small samples or
  extensive tied ranks; the API emits a warning in those cases.
- Simple linear regression is exploratory. It treats selected numerical rating
  levels as approximately equally spaced and therefore requires cautious
  interpretation for ordinal measures.
- If the selected data support the other analysis but regression is unavailable,
  the API returns a stable regression object containing null numerical results
  and a clear reason instead of fabricating values or discarding other results.
- Correlation and regression describe association, not causation. Results from
  this sample must not be generalized to every Indian student.

## Known limitations

- The internet-facility rating is subjective and ordinal. It is not measured
  download/upload speed, latency, reliability, or Mbps.
- The source schema contains no explicit network-interruption-frequency field.
- Cross-sectional survey data can show associations but does not establish
  causation.
- The numeric direction of the five-level fields is not explicitly mapped to
  labels inside the CSV; interpretations involving “better” or “worse” require
  the source scale direction to be confirmed.
- The meaning and spacing of the nine observed online-performance values require
  caution when used in exploratory regression.
- Any later handling of potential confounders or subgroup comparisons must be
  documented rather than assumed.

## Phase 3 integration notes

The preview endpoint provides exact columns for variable selectors. The analysis
endpoint returns stable nested objects for summary cards, correlation,
regression, hypothesis testing, scatter points, a regression line, and frequency
data. Chart payloads are deterministically limited to 500 points while all valid
pairs remain in the statistical calculations.
