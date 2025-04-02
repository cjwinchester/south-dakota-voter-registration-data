# South Dakota voter registration data
This repository contains county-level voter registration data for South Dakota, broken down by party.

_Updated April 1, 2025_

The data -- 169 snapshots in time -- comes from the South Dakota Secretary of State's website:
- [December 2015 to present](https://sdsos.gov/elections-voting/upcoming-elections/voter-registration-totals/voter-registration-by-county.aspx): Monthly snapshots, plus election totals
- June 1976 to November 2014 ([source 1](https://sdsos.gov/elections-voting/election-resources/election-history/election-history-search.aspx), [source 2](https://sdsos.gov/elections-voting/election-resources/election-history/official-election-returns.aspx)): Election totals, typically less detailed than current data

[Here's a spreadsheet](https://docs.google.com/spreadsheets/d/10pmZWif5diKq39cQDo4G5NTov3Y5k_FZ-7pHfBYpAJg/edit?usp=sharing) with a complete list of sources. [I use pdfplumber to parse the monthly reports](Parse%20SD%20monthly%20voter%20registration%20report.ipynb).

Files are named after the snapshot date in `YYYY-MM-DD.*` format. Individual CSV files live in the [`data`](data) folder. The original PDFs, some of them rendered from web pages, live in the [`pdfs`](pdfs) folder.

The [`build_files.py`](build_files.py) script creates two (tidy) combined files, each with two new columns -- `county_fips`, derived from looking up county names in the `us-county-fips.csv` file, and `election`, which lists the type of election for that snapshot date, if applicable, sourced from a file I created, `elex-lookup.json`:
- [`sd-voter-registration-data.csv`](sd-voter-registration-data.csv): The columns in this file are `date,county,county_fips,party,voters,election` -- note that _inactive_ is sometimes the "party" name, so if your goal is to analyze active voter registration, you'd need to filter these out first.
- [`sd-voter-registration-data-simplified.csv`](sd-voter-registration-data-simplified.csv): Same as above, except:
    - All non-Republican/Democratic party categories are collapsed into a single "other" category
    - Inactive records are removed
    - Two snapshot records for Washabaugh County, which merged with Jackson County in 1983, are removed
    - Records for Shannon County, which was renamed Oglala Lakota County in 2015, are renamed with the current county name and given the associated FIPS code
