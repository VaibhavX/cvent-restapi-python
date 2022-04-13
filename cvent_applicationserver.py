''''Program that authenticates CVENT Application with the Access token stores in S3 Bucket
    and then retrieves user registered in the course list present in the csv files using Pandas
    Upload the final file in S3 Bucket for LMS Processing.'''

'''Code built in Cloud9 - hence AWS Credentials are already authenticated. If built in LOCAL IDE, authenticate AWS'''

import boto3
import pandas as pd
import requests
import json
from botocore.errorfactory import ClientError
from io import StringIO

s3 = boto3.resource('s3')

s3_object = s3.Bucket('S3 BUCKET NAME').Object('S3 FILE NAME').get()
file_content = s3_object['Body'].read().decode() #Decoded as String

#Converting back to json file and extracting token
json_content = json.loads(file_content)
access_token = json_content['access_token']

app_server = "CVENT APPLICATION SERVER URL"

headers = {
    'Accept':'application/json',
    'Authorization': f'Bearer {access_token}'
}

#Access Token Validation
def token_validation():
    validatation_url =app_server+"token-validation"
    response = requests.get(validatation_url, headers= headers)
    assert response.status_code == 200, response.text
    #print(response)


#Get Program Id of On Demand Courses
def get_programid():
    program_id_list =[]
    events_url = app_server+"events/filter"
    #Filtering only Events which are still Active and not Completed, Archived or Cancelled.
    data = {
        "filter":"eventStatus eq 'Upcoming'"
    }
    response = requests.post(events_url, headers=headers, json=data)
    assert response.status_code ==200, response.text

    list_of_programs = response.json()['data']
    
    #Reading List of Programs from the CSV File - makes it scalable to any number of programs
    df = pd.read_csv('LOCAL FILE PROGRAM LIST --- SUBSTITUITE FOR S3 FILE IF AVAILABLE')
    for program_name in df['Program List']: 
        for i in range(len(list_of_programs)):
            if list_of_programs[i]['title'] == program_name:
                program_id_list.append(list_of_programs[i]['id'])
                break
    
    return program_id_list

#Get List of Attendees in the Program
def attendee_list(program_id):
    
    attendee_url = app_server+"attendees/filter"
    id_ctr = 0 #Counter to iterate through Program ID List
    
    #Create the dataframe here
    column_names = ["email", "first_name", "last_name", "organization", "job_title", "program_name"]
    df = pd.DataFrame(columns=column_names)
    
    s3_object = s3.Bucket('S3 BUCKET NAME').Object('S3 FILE NAME').get() #File Name here is the Program_List.csv stored in S3 bucket
    file_content = s3_object['Body'].read().decode() #Decoded as String
    programs = pd.read_csv(StringIO(file_content)
    
    for program_name in programs['Program List']:
   
        data = {
            "filter":f"event.id eq '{program_id[id_ctr]}'"
     }
        response=requests.post(attendee_url, headers=headers, json=data)
        assert response.status_code == 200, response.text

        list_of_attendees = response.json()['data']

    
        for i in range(len(list_of_attendees)):
            if list_of_attendees[i]['status']=="Accepted":
                current_user = {
                    'email': list_of_attendees[i]['contact']['email'],
                    'first_name':list_of_attendees[i]['contact']['firstName'],
                    'last_name':list_of_attendees[i]['contact']['lastName'],
                    'organization':list_of_attendees[i]['contact']['company'],
                    'job_title':list_of_attendees[i]['contact']['title'], 
                    'program_name':program_name
                }
                df2 = pd.DataFrame(data=current_user, index=[0])
                df = pd.concat([df, df2], ignore_index=True)
        id_ctr = id_ctr + 1
    
    return df
    #Upload DataFrame to S3 Bucket here and return a success message after returning DataFrame


#Calling everything in order from main
def main():
    #Authenticating Access Token
    token_validation()
    
    #Get Program Id for Program
    program_ids = get_programid()
    
    #Get Registrant dataframe
    cvent_dataframe = attendee_list(program_ids)
    print("Registration List Generated in Root Directory")
    cvent_dataframe.to_csv('FINAL OUTPUT -- REGISTRATION LIST IN CSV', sep='\t')
    
    
    #Uploading Registration List Generated to S3 bucket
    s3.Object('S3 BUCKET NAME', 'S3 FILENAME').put(Body=open("GENERATED REGISTRATION LIST", 'rb'))
    
    #Verifying if file is successfully uploaded
    try:
        s3.Object('S3 BUCKET NAME','S3 FILE NAME.csv').load()
    except ClientError as e:
        if e.response['Error']['Code'] == 404:
            print("Object Does not Exist")
        else:
            print("Error in Load Process")
            raise
    else:
        print("Object exists")


if __name__=='__main__':
    main()



    
