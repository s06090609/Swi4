# ''' Importing libraries'''
from __future__ import print_function
import os.path
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
import io
from googleapiclient.errors import HttpError
import pickle
import shutil
from mimetypes import MimeTypes
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import psycopg2
import time
from io import BytesIO
import pandas as pd
import numpy as np



class Table():
    
    def __init__(self):
        self.auth=self.first_authentification()


        # periodicity_time=24*(60**2)
        periodicity_time=3 # 24 hours in seconds
        while True:
            self.FLE=self.download_file()
            self.df=self.convert_data()
            self.create_db_and_add_data()
            time.sleep(periodicity_time)


    def first_authentification(self):

        self.SCOPES = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']

        """Shows basic usage of the Drive v3 API.
        Prints the names and ids of the first 10 files the user has access to.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        print('Initial authentification is done')

        try:
            service = build('drive', 'v3', credentials=creds)

            # Call the Drive v3 API
            results = service.files().list(
                pageSize=10, fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])

            if not items:
                print('No files found.')
                return
            print('Files:')
            for item in items:
                print(u'{0} ({1})'.format(item['name'], item['id']))
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')


    
    def download_file(self):
        ''' creating function to download data from google drive'''
        google_file_id ='1abkOn29tonFO4-Up-5IAXzUEanYwNnW9QfC0Y1gQwUY'
        creds = None


        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())


        try:
            # create drive api client
            service = build('drive', 'v3', credentials=creds)

            file_id = google_file_id

            request = service.files().export_media(fileId=file_id,
                                                    mimeType='text/tab-separated-values'
                                                )
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request
            )

            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(F'Download {int(status.progress() * 100)}.')
            

            
            # time.sleep(5)
            # download_file(real_file_id)

        except HttpError as error:
            print(F'An error occurred: {error}')
            file = None

        return file.getvalue()

    def convert_data(self):
        '''Convert data from google drive into pandas DataFrame
        and prepare data in correct format'''
        s=str(self.FLE,'utf-8') ### decoding bytes data and converting into strings
        split_data=s.split('\t') ### splitting the data to get 
        cols=split_data[:4] ### pulling columns names from data
        cols[-1]='срок поставки' # creating additional clumn
        df=pd.DataFrame(columns=cols)

        ''' rearanging columns and values in pandas data Frame format'''

        n_cols=len(cols)
        data_ind=0
        for i in range(len(cols)-1):
            df[f'{cols[i+1]}']=split_data[n_cols+data_ind::3]
            data_ind+=1
        df['№']=(df.index+1).astype(str)

        ''' getting rid of \r\n#'''
        for i in range(len(df)):
            df['срок поставки'].iloc[i]=df['срок поставки'].iloc[i][:10]

        ''' Pulling current rub/usd exchange rate'''
        data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
        rub_usd_exchange=data['Valute']['USD']['Value']


        ''' Applying current rub/usd exchange rate to calculate the price in rubles'''
        df['стоимость в руб']=df['стоимость,$'].astype(float)*rub_usd_exchange

        print('Data preparation is done')
        return df


    
    def create_db_and_add_data(self):
        try:
            conn = psycopg2.connect(
            database="unwind_digital_db",
                user='postgres',
                password='admin',
                host='192.168.0.108', #'localhost', #
                port= '5432'
            )
            conn.autocommit = True
            # Creating a cursor object
            cur = conn.cursor()
            #Creating DataBase for Unwind Digital data
            try:
                db= ''' CREATE database Unwind_digital_db '''
                cur.execute(db)
            except:
                pass

            cur.execute('DROP TABLE IF EXISTS test')

            create_script=''' CREATE TABLE IF NOT EXISTS test (
                "№" int PRIMARY KEY,
                "заказ №"    int,
                "стоимость,$"   int,
                "срок поставки" date,
                "стоимость в руб" float)'''

            cur.execute(create_script)

            insert_script=' INSERT INTO test ("№","заказ №", "стоимость,$", "срок поставки" ,"стоимость в руб") VALUES (%s, %s, %s, %s, %s)'
            insert_values=list(map(tuple, self.df.values)) #df.iloc[1].values#df.iloc[0].astype(float)# #

            for record in insert_values:
                cur.execute(insert_script,record)
            print('Data upload is done')
            # print('done2')
            conn.commit()
            cur.close()
        except Exception as error:
            print (error)

# if __name__ == '__main__':
#     FLE=download_file('1abkOn29tonFO4-Up-5IAXzUEanYwNnW9QfC0Y1gQwUY')
    
Table()

