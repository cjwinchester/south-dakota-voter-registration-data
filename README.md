# South Dakota voter registration data
This repository contains county-level voter registration data for South Dakota, broken down by party.

_Updated February 23, 2023_

The data -- 142 snapshots in time -- comes from the South Dakota Secretary of State's website:
- [December 2015 to present](https://sdsos.gov/elections-voting/upcoming-elections/voter-registration-totals/voter-registration-by-county.aspx): Monthly snapshots, plus election totals
- June 1976 to November 2014 ([source 1](https://sdsos.gov/elections-voting/election-resources/election-history/election-history-search.aspx), [source 2](https://sdsos.gov/elections-voting/election-resources/election-history/official-election-returns.aspx)): Election totals, typically less detailed

[Here's a spreadsheet](https://docs.google.com/spreadsheets/d/10pmZWif5diKq39cQDo4G5NTov3Y5k_FZ-7pHfBYpAJg/edit?usp=sharing) with a complete list of sources.

Files are named after the snapshot date in `YYYY-MM-DD.*` format. Individual CSV files live in the [`data`](data) folder. The original PDFs, some of them rendered from web pages, live in the [`pdfs`](pdfs) folder.

The [`build_files.py`](build_files.py) script creates two combined files with a new column, `county_fips`:
- [`sd-voter-registration-data-long.csv`](sd-voter-registration-data-long.csv) (tidy format)
- [`sd-voter-registration-data-wide.csv`](sd-voter-registration-data-wide.csv) (wide format)