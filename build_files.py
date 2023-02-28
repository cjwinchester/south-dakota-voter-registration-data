import csv
import json
import glob


def get_elex_lookup():
    with open('elex-lookup.json', 'r') as infile:
        return json.load(infile)


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

    lookup_fips = get_fips_lookup()
    lookup_elex = get_elex_lookup()

    data_filepath = 'sd-voter-registration-data.csv'
    data_filepath_simplified = 'sd-voter-registration-data-simplified.csv'

    files = glob.glob('data/*.csv')

    data_out = []
    data_out_simplified = {}

    for file in files:

        elex = lookup_elex.get(file.split('/')[-1].split('.')[0])
        
        with open(file, 'r') as infile:
            reader = csv.DictReader(infile)

            for row in reader:
                date = row.get('date')
                county = row.get('county')
                fips = lookup_fips[county]

                if not data_out_simplified.get(date):
                    data_out_simplified[date] = {}

                if not data_out_simplified.get(date).get(fips):

                    data_out_simplified[date][fips] = {
                        'county': county,
                        'election': elex,
                        'republican': 0,
                        'democratic': 0,
                        'other': 0
                    }

                for header in list(row.keys()):
                    if header not in ['date', 'county']:

                        votes = row.get(header) or 0
                        votes = int(votes)

                        data_out.append({
                            'date': date,
                            'county': county,
                            'county_fips': fips,
                            'party': header,
                            'voters': votes,
                            'election': elex
                        })

                        # simplified file doesn't need inactive records
                        if header == 'inactive':
                            continue

                        # collapse non-R/D parties into "other"
                        if header not in ['republican', 'democratic']:
                            header = 'other'

                        data_out_simplified[date][fips][header] += votes

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

    data_out_simplified_records = []

    for date in data_out_simplified:
        fips_codes = data_out_simplified[date]

        for fips in fips_codes:
            rec = fips_codes[fips]
            county = rec.get('county')
            elex = rec.get('election')

            # skip Washabaugh records
            if county == 'Washabaugh':
                continue

            # update shannon/oglala
            if county == 'Shannon' and int(fips) == 46113:
                county = 'Oglala Lakota'
                fips = '46102'

            for header in list(rec.keys()):

                if header not in ['county', 'election']:
                    data_out_simplified_records.append({
                        'date': date,
                        'county': county,
                        'county_fips': fips,
                        'party': header,
                        'voters': int(rec.get(header)),
                        'election': elex
                    })

    data_out_simplified_sorted = sorted(
        data_out_simplified_records,
        key=lambda x: (
            x['date'],
            x['county_fips'],
            x['party']
        )
    )

    with open(data_filepath_simplified, 'w') as outfile:
        writer = csv.DictWriter(
            outfile,
            fieldnames=list(data_out_simplified_sorted[0].keys())
        )

        writer.writeheader()

        writer.writerows(data_out_simplified_sorted)

    print(f'Wrote {data_filepath_simplified}')


if __name__ == '__main__':
    build_files()
