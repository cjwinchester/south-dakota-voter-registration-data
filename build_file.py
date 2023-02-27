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


def build_file():

    lookup = get_fips_lookup()

    data_filepath = 'sd-voter-registration-data.csv'

    files = glob.glob('data/*.csv')

    data_out = []

    for file in files:
        with open(file, 'r') as infile:
            reader = csv.DictReader(infile)

            for row in reader:
                date = row.get('date')
                county = row.get('county')
                fips = lookup[county]

                for header in list(row.keys()):
                    if header not in ['date', 'county']:
                        data_out.append({
                            'date': date,
                            'county': county,
                            'county_fips': fips,
                            'party': header,
                            'voters': row.get(header)
                        })

                row['county_fips'] = fips

    data_sorted = sorted(
        data_out,
        key=lambda x: (
            x['date'],
            x['county_fips'],
            x['party']
        )
    )

    with open(data_filepath, 'w') as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=list(data_sorted[0].keys())
        )

        writer.writeheader()
        writer.writerows(data_sorted)

    print(f'Wrote {data_filepath}')


if __name__ == '__main__':
    build_file()
