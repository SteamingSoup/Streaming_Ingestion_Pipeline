from faker import Faker # package used to generate fake data
import psycopg2 # database adapter for python so communicate with PostgreSQL database using python
from time import sleep # suspends execution for so many seconds
from datetime import datetime # for manipulating dates and times
import pandas as pd
from sqlalchemy import create_engine # creates new engine object

if __name__ == '__main__': # if file is run directly
    conn = create_engine("postgresql://TEST:password@localhost/TEST") # create engine
    faker = Faker()       ## //user:password@hostname/database_name
    fields = ['job','company','residence','username','name','sex','address','mail','birthdate','ssn']
    i = 0

    while True: 
        data = faker.profile(fields) # using faker to generat e basic profile information based on fields list
        data['timestamp'] = datetime.now() # creating timestamp that is the current local time
        df = pd.DataFrame(data, index = [i]) # creating dataframe from generate profile information in data object
        print(f"Inserting data {data}")
        df.to_sql('USERS',conn, if_exists='append') # creates new tables 'USERS' using conn engine
        i +=1 # i adding 1 to i variable and assigning result to that variable
        sleep(1) # every one second
