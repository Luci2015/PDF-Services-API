import json
from time import sleep

import requests

# USING OAUTH S2S credentials
client_id = 'your client id'
client_secret = 'your client secret'
source_pdf = 'abs path to source pdf'

# GETTING AUTHORIZED
ims_url = 'https://ims-na1.adobelogin.com/ims/token/v3'
payload = ('grant_type=client_credentials'
           '&client_id=' + client_id + \
           '&client_secret=' + client_secret + \
           '&scope=openid,AdobeID,DCAPI')
headers = {
  'Accept': 'application/json',
  'Content-Type': 'application/x-www-form-urlencoded'
}
response = requests.request('POST', ims_url, headers=headers, data=payload)
token = response.json()['access_token']

# OBTAIN THE assetID AND uploadUri (using US datacenter asset url below)
asset_url = 'https://pdf-services-ue1.adobe.io/assets'
headers = {'x-api-key': client_id, 
           'Authorization': 'Bearer ' + token,
           'Content-Type': 'application/json'}
body = json.dumps({'mediaType': 'application/pdf'})
r = requests.post(asset_url, headers=headers, data=body)
if r.status_code > 200:
   print(r.text)
r_json = json.loads(r.text)
upload_uri = r_json['uploadUri']
asset_id = r_json['assetID']

# UPLOAD THE PDF TO DESIGNATED uploadUri
hh = {'Content-Type':'application/pdf'}
with open(source_pdf, 'rb') as f:
   data = f.read()
upload_asset = requests.put(upload_uri, headers=hh, data=data)
print('upload PDF status code: ', upload_asset.status_code)

# CALL THE EXPORT TO DOCX API (using US datacenter below)
export_url = 'https://pdf-services-ue1.adobe.io/operation/exportpdf'
body = { 'assetID': asset_id,
         'targetFormat': 'docx',
         'ocrLang': 'en-US'
}
response = requests.post(export_url, headers=headers, data=json.dumps(body))
print(response.text)
print('status poll location: ', response.headers['location'])

""" POLL STATUS URL UNTIL JOB IS DONE
a successful response would look like this:
{
  "status": "done",
  "asset": {
    "metadata": {
      "type": "application/pdf",
      "size": 200791
    },
    "downloadUri": "https://dcplatformstorageservice.......",
    "assetID": "urn:aaid:AS:........"
  }
}
"""
if str(response.status_code) == '201':
   #poll results
   poll_url = response.headers['location']
   done = False
   call_nb = 0
   while not done:
      call_nb += 1
      print('Attempt {} to poll status URL'.format(call_nb))
      response = requests.get(poll_url, headers=headers)
      status = json.loads(response.text)['status']
      if status == 'in progress':
         done = False
         sleep(3)
         print('pausing 3 seconds')
      elif status == 'done':
         done = True
         # ADD YOUR OWN LOGIC HERE TO SAVE THE FILE
         print('download docx from here: \n', 
               json.loads(response.text)['asset']['downloadUri'])
      else:
         # some problem, see response text and headers
         done = True
         print(response.text)
         print(response.headers)

