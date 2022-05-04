''''Program to generate Access Token for a CVENT SERVER. IMP --- It uses Base64 Encoding'''

'''Code built inside AWS Cloud9, hence bypassing AWS Credentials. If you are using Local IDE, add AWS Credentials'''

#Authenticating CVENT --- Retrieving Access Token
import base64
import requests
import json
import boto3
from botocore.errorfactory import ClientError

s3 = boto3.client('s3')
client = boto3.client('ssm')

sandbox_url = '''Enter CVENT TARGET URL HERE'''

client_id =(client.get_parameter(Name="CLIENT ID", WithDecryption=True))['Parameter']['Value']
client_secret =(client.get_parameter(Name="CLIENT SECRET", WithDecryption=True))['Parameter']['Value']
version = 'ea'
userpass = client_id +':'+client_secret
encoded_u = base64.b64encode(userpass.encode()).decode()

headers = {
    'Content-Type' : 'application/x-www-form-urlencoded',
    'Authorization': 'Basic %s' % encoded_u
}

data = {
    'grant_type' : 'client_credentials',
    'client_id': (None, client_id)
}

target_url = sandbox_url + "/" + version + "/oauth2/token"
#print(target_url)
response = requests.post(target_url, headers= headers, data=data)
assert response.status_code == 200, response.text

json_response = response.json()

access_token = json_response['access_token']
print(access_token)

#Adding Access Token Response to Json File on root
json_object = json.dumps(json_response, indent = 4)

#Save a copy of Json Reponse on Local Directory
with open("""FILE NAME""", "w") as outfile:
    outfile.write(json_object)

#Uploading Json File to S3
with open("""FILE NAME""", "rb") as f:
    s3.upload_fileobj(f, """S3 BUCKET NAME""", """S3 FILE NAME""")
    
#Testing if file successfully uploaded to S3
try:
    s3.head_object(Bucket ='''S3 BUCKET NAME''',Key = '''S3 FILE NAME''' )
except ClientError as e:
    if e.response['Error']['Code'] == 404:
        print("Object Does not Exist")
    else:
        print("Error in Load Process")
        raise
else:
    print("Object exists")
