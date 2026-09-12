# South Dakota voter registration data
This repository contains county-level voter registration data for South Dakota, broken down by party.

_Updated September 12, 2026_

The data -- 187 snapshots in time -- comes from the South Dakota Secretary of State's website:
- [December 2015 to present](https://sdsos.gov/elections-voting/upcoming-elections/voter-registration-totals/voter-registration-by-county.aspx): Monthly snapshots, plus election totals
- June 1976 to November 2014 ([source 1](https://sdsos.gov/elections-voting/election-resources/election-history/election-history-search.aspx), [source 2](https://sdsos.gov/elections-voting/election-resources/election-history/official-election-returns.aspx)): Election totals, typically less detailed than current data

[I use pdfplumber to parse the monthly reports](Parse%20SD%20monthly%20voter%20registration%20report.ipynb).

Files are named after the snapshot date in `YYYY-MM-DD.*` format. Individual CSV files live in the [`data`](data) folder. The original PDFs, some of them rendered from web pages, live in the [`pdfs`](pdfs) folder.

[`Build files.ipynb`](Build%20files.ipynb) turns those individual snapshot files into two tidy combined CSV files, each with two new columns -- `county_fips`, derived from looking up county names in the `us-county-fips.csv` file, and `election`, which lists the type of election for that snapshot date, if applicable, sourced from a file I created, `elex-lookup.json`:
- [`south-dakota-voter-registration-data.csv`](south-dakota-voter-registration-data.csv): The columns in this file are `date,county,county_fips,party,voters,election` -- note that _inactive_ is sometimes the "party" name, so if your goal is to analyze active voter registration, you'd need to filter these out first.
- [`south-dakota-voter-registration-data-simplified.csv`](south-dakota-voter-registration-data-simplified.csv): Same as above, except:
    - All non-Republican/Democratic party categories are collapsed into a single "other" category
    - Inactive records are removed
    - Two snapshot records for Washabaugh County, which merged with Jackson County in 1983, are removed
    - Records for Shannon County, which was renamed Oglala Lakota County in 2015, are renamed with the current county name and given the associated FIPS code

The same notebook also builds [`_site/south-dakota-voter-registration.json`](_site/south-dakota-voter-registration.json), a statewide-and-by-county breakdown formatted for Chart.js, which powers [this chart](_site/index.html), which was built by Claude.

## Notes
- **2026-09-01 snapshot correction:** Republican and Democratic column labels were transposed in the PDF for the September 2026 report (`pdfs/2026-09-01.pdf`), probably because this was a reversion to an older column layout after the July 2026 report used a different one. `data/2026-09-01.csv` has been corrected at the source, so the swap doesn't need to be re-applied downstream.