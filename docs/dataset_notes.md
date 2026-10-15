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

These are structural inspection findings only. No statistical analysis was
performed in Phase 1.

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
scales as ranging from very bad to very good. The CSV itself contains numbers
but no embedded codebook, so that direction should be explicitly confirmed in
Phase 2 before encoding.

## Known limitations

- The internet-facility rating is subjective and ordinal. It is not measured
  download/upload speed, latency, reliability, or Mbps.
- The source schema contains no explicit network-interruption-frequency field.
- Cross-sectional survey data can show associations but does not establish
  causation.
- Category labels, ordinal direction, and the nine observed performance values
  must be validated before selecting Phase 2 methods or encodings.
- Any later handling of potential confounders or subgroup comparisons must be
  documented rather than assumed.

## Pending preparation for Phase 2

1. Confirm scale direction and value-label semantics against source metadata.
2. Define explicit validation rules without changing the original CSV.
3. Choose justified encodings for ordinal and categorical fields.
4. Create a cleaned working copy in a separate file only if Phase 2 requires it.
5. Select statistical methods appropriate to the verified scales and project
   research question.
