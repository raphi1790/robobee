import hashlib
import hmac
import time
import requests
import uuid
import sys
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv()

client_id = os.environ.get('CLIENT_ID')
api_key = os.environ.get('API_KEY')
API_SECRET = str.encode(os.environ.get('API_SECRET'))

print("client_id", client_id)
print("api_key", api_key)
print("api_secret",API_SECRET )
  

timestamp = str(int(round(time.time() * 1000)))
nonce = str(uuid.uuid4())
content_type = 'application/x-www-form-urlencoded'
payload = {'offset': '1'}

if sys.version_info.major >= 3:
    from urllib.parse import urlencode
else:
    from urllib import urlencode

payload_string = urlencode(payload)

# '' (empty string) in message represents any query parameters or an empty string in case there are none
message = 'BITSTAMP ' + api_key + \
    'POST' + \
    'www.bitstamp.net' + \
    '/api/v2/balance/etheur/' + \
    '' + \
    content_type + \
    nonce + \
    timestamp + \
    'v2' + \
    payload_string
message = message.encode('utf-8')
signature = hmac.new(API_SECRET, msg=message, digestmod=hashlib.sha256).hexdigest()
headers = {
    'X-Auth': 'BITSTAMP ' + api_key,
    'X-Auth-Signature': signature,
    'X-Auth-Nonce': nonce,
    'X-Auth-Timestamp': timestamp,
    'X-Auth-Version': 'v2',
    'Content-Type': content_type
}
r = requests.post(
    'https://www.bitstamp.net/api/v2/balance/etheur/',
    headers=headers,
    data=payload_string
    )
if not r.status_code == 200:
    raise Exception('Status code not 200')

string_to_sign = (nonce + timestamp + r.headers.get('Content-Type')).encode('utf-8') + r.content
signature_check = hmac.new(API_SECRET, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
if not r.headers.get('X-Server-Auth-Signature') == signature_check:
    raise Exception('Signatures do not match')

print(r.content)