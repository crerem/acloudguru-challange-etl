import json
import psycopg2
import pandas as pd
import os
import boto3
from data_transformation import data_transformation

ny_url = 'https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv'
jh_url = 'https://raw.githubusercontent.com/datasets/covid-19/master/data/time-series-19-covid-combined.csv'

database_endpoint = os.environ['endpoint']
database_name= os.environ['database']
database_user=os.environ['user']
database_pass=os.environ['password']
sns_arn=os.environ['sns_arn']



CONNECT_DB = "host="+database_endpoint+" port=5432 dbname="+database_name+" user="+database_user+" password="+database_pass+" "


def create_tables2(Prepared_Data):
  create_tables_query='''CREATE TABLE covid_table (ondate date PRIMARY KEY, cases integer, deaths integer, recovered integer);'''
  try:
    cxn=psycopg2.connect(CONNECT_DB)
    cur=cxn.cursor()
    cur.execute(create_tables_query)
    records=cxn.commit()
  except (Exception,psycopg2.Error) as error:
     sns_motification( "Error while creating table {}",format(error) )
  finally:
    if(cxn):
      cur.close()
      cxn.close()
      #print ("Connection closed")
  #insert data
  initial_insert(Prepared_Data)







def populate_database(Prepared_Data):
  #if results is None - meaning no table - let's create the table
  if(db_table_exists()):
    #if table exist - let's add the last row
    try:
      if(check_if_last_date_exist(Prepared_Data)):
        #exist
        print('row exists')
      else:
        insert_new_row(Prepared_Data)
    except Exception as e:
      sns_motification( "Error  {}",format(error) )
      exit(1);
  else:
    #table does not exist - let's create it
    create_tables2(Prepared_Data)






def db_table_exists():
   check_query='''select * from information_schema.tables where table_name=%s;'''
   try:
     cxn=psycopg2.connect(CONNECT_DB)
     cur=cxn.cursor()
     cur.execute(check_query,('covid_table',))
     #print(cur.rowcount)
     return bool(cur.rowcount)
   except (Exception,psycopg2.Error) as error:
      sns_motification( "Error when checking if table exist {}",format(error) )





def check_if_last_date_exist(Prepared_Data):
   from datetime import date
   cxn=psycopg2.connect(CONNECT_DB)
   cxn.autocommit=True
   cur=cxn.cursor()

   last_item = Prepared_Data["date"].iloc[-1]
   #print('we add '+ last_item.strftime("%m/%d/%Y") )
   last_row_query="SELECT * FROM covid_table WHERE ondate=%s;"
   try:
     cur.execute(last_row_query, (last_item,) )
     #print(cur.rowcount)
     return bool(cur.rowcount)
   except (Exception,psycopg2.Error) as error:
     sns_motification( "Error checking if last data exist {}",format(error) )
   finally:
     if(cxn):
       cur.close()
       cxn.close()
       #print ("Connection closed")



def sns_motification(sns_message):
    try:
        sns = boto3.client('sns')
        sns.publish(TopicArn =sns_arn, Message = sns_message)
    except Exception as e:
        print("SNS was not sent {}".format(e))
        exit(1)




def lambda_handler(event, context):
    sns_motification( "Start execution" )
    #data extranction
    NewYork_Data  = pd.read_csv( ny_url)
    JohnHope_Data  = pd.read_csv( jh_url, usecols=['Date','Country/Region','Recovered']);

    #data transofromation
    try:
        Prepared_Data = data_transformation(NewYork_Data,JohnHope_Data)
    except Exception as e:
        sns_motification( "Data Transformation error {}",format(error) )
        exit(1)

    #print (Prepared_Data)
    populate_database(Prepared_Data);








def insert_new_row(Prepared_Data):
   data=[];
   row = (Prepared_Data["date"].iloc[-1], int(Prepared_Data["cases"].iloc[-1]),int(Prepared_Data["deaths"].iloc[-1]),int(Prepared_Data["recovered"].iloc[-1]))

   records ="%s"
   data.append(row)
   #print(data)
   #print(row)

   insert_query = "insert into covid_table(ondate,cases,deaths,recovered)  values{}".format(records);

   cxn=psycopg2.connect(CONNECT_DB)
   cxn.autocommit = True
   cur=cxn.cursor()
   try:
       cur.execute(insert_query, data )
       cxn.commit()
   except (Exception,psycopg2.Error) as error:
     sns_motification( "Error while inserting a new row {}",format(error) )
   finally:
     if(cxn):
       cur.close()
       cxn.close()



def initial_insert(Prepared_Data):
   #print ('table exist - do the inital insert ');
   data = [];

   for i in Prepared_Data.index:
     row = (Prepared_Data.loc[i,'date'], int(Prepared_Data.loc[i,'cases']),int(Prepared_Data.loc[i,'deaths']),int(Prepared_Data.loc[i,'recovered']))
     data.append(row)

   records = ','.join(['%s'] * len(data))
   insert_query = "insert into covid_table(ondate,cases,deaths,recovered) values{}".format(records)

   # print (data)
   cxn=psycopg2.connect(CONNECT_DB)
   cxn.autocommit = True
   cur=cxn.cursor()

   try:
       cur.execute(insert_query,data)
       cxn.commit()

   except (Exception,psycopg2.Error) as error:
     sns_motification( "Error on initial insert {}",format(error) )
   finally:
     if(cxn):
       cur.close()
       cxn.close()
