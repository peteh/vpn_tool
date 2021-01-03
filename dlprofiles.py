#!/bin/python

import requests
import os
import re
from urllib.parse import urlparse

RESTRICTED_PAGE = 'https://support.nordvpn.com/Restricted-countries/1391702632/Connecting-from-countries-with-internet-restrictions-on-Windows.htm'

def downloadFile(url):
    print('Downloading file: ' + url)
    r = requests.get(url)
    parsed = urlparse(url)
    fileName = os.path.basename(parsed.path)
    with open(fileName, 'wb') as f:
        f.write(r.content)
    print('Finished download: ' + url)
#


page = requests.get(RESTRICTED_PAGE)
urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', page.text)
for url in urls:
    if url.endswith('.ovpn'):
        downloadFile(url)
