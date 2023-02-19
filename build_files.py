import csv
import glob


def get_fips_lookup():
    with open('us-county-fips.csv', 'r') as infile:
        reader = csv.DictReader(infile)

        sd = [x for x in reader if x['state_fips'] == '46']

        lookup = {}

        for county in sd:
            fips = f'{county.get("state_fips")}{county.get("county_fips")}'

            name = county.get('county_name').replace(' County', '')
        
            lookup[name] = fips

    lookup['Oglala Lakota'] = '46102'

    lookup['Washabaugh'] = '46131'

    return lookup


def build_files():

    lookup = get_fips_lookup()

    data_filepath_long = 'sd-voter-registration-data-long.csv'
    data_filepath_wide = 'sd-voter-registration-data-wide.csv'

    files = glob.glob('data/*.csv')

    long_data = []
    wide_data = []

    headers_wide = [
        'date',
        'county',
        'county_fips'
    ]

    headers_wide_set = set()

    for file in files:
        print(file)
        with open(file, 'r') as infile:
            reader = csv.DictReader(infile)

            for row in reader:
                date = row.get('date')
                county = row.get('county')
                fips = lookup[county]
                print(county, fips, date)

                for header in list(row.keys()):
                    if header not in ['date', 'county']:
                        long_data.append({
                            'date': date,
                            'county': county,
                            'county_fips': fips,
                            'party': header,
                            'voters': row.get(header)
                        })

                row['county_fips'] = fips
                wide_data.append(row)
                headers_wide_set.update(
                    [x for x in list(row.keys()) if x not in headers_wide]
                )

    data_sorted_long = sorted(
        long_data,
        key=lambda x: (
            x['date'],
            x['county_fips'],
            x['party']
        )
    )

    data_sorted_wide = sorted(
        wide_data,
        key=lambda x: (
            x['date'],
            x['county_fips']
        )
    )

    with open(data_filepath_long, 'w') as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=list(data_sorted_long[0].keys())
        )

        writer.writeheader()
        writer.writerows(data_sorted_long)

    print(f'Wrote {data_filepath_long}')

    with open(data_filepath_wide, 'w') as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=headers_wide + sorted(list(headers_wide_set))
        )

        writer.writeheader()
        writer.writerows(data_sorted_wide)

    print(f'Wrote {data_filepath_wide}')


if __name__ == '__main__':
    build_files()
