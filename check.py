import os
import csv
import time
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil.parser import parse
from slack_sdk.webhook import WebhookClient


URL = 'https://sdsos.gov/elections-voting/upcoming-elections/voter-registration-totals/voter-registration-by-county.aspx'
webhook = WebhookClient(
    os.environ.get('SLACK_HOOK_STATE_ELECTIONS')
)


def check_for_new_reports():

    dates_completed = [datetime.fromisoformat(x.stem).date() for x in Path('data').glob('*.csv')]

    r = requests.get(
        URL,
        headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0'
        }
    )

    r.raise_for_status()
    time.sleep(1)

    soup = BeautifulSoup(r.text, 'html.parser')
    center = soup.find('section', {'class': 'centerer'})
    links = center.find_all('a')

    new_reports = []

    for link in links:
        label = ' '.join(
            link.text.split()
        )

        url = urljoin(
            URL,
            link.get('href')
        )

        if '12.2.2015.pdf' in url:
            continue

        try:
            report_date = parse(label).date()
        except:
            if '06.05.2018' in url:
                urldate = '06.05.2018'
            else:
                urldate = Path(url).stem.split('_')[-1].split(' ')[-1].split('County')[-1]
            report_date = parse(urldate).date()

        if report_date in dates_completed:
            continue

        new_reports.append({
            'label': label,
            'url': url
        })

    if not new_reports:
        return []

    response = webhook.send(
        text=f'New voter registration data: {" | ".join([x.get("url") for x in new_reports])}',
        blocks=[
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "New S.D. voter registration data"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": '\n'.join(
                        [f'- <{x.get("url")}|{x.get("label")}>' for x in new_reports]
                    )
                }
            }
        ]
    )
    
    time.sleep(1)

    return new_reports


if __name__ == '__main__':
    check_for_new_reports()
