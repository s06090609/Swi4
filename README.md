# Unwind_Digital_test

1)Download and unzip files in your preffered location ( The "Token.json" and "unwind_digital_test.py" MUST BE IN THE SAME FOLDER)

2)Create your own DataBase in PostgreSQL with following properties:
database="unwind_digital_db",
user='postgres',
password='admin',
host='localhost',
port= '5432'

2)run the "unwind_digital_test.py"

3)If There are expired orders, the notification will be sent in telegram to https://t.me/Expired_orders_bot

4)Each Stage of the Script will print message notifying of stage completion


Warning!

There is no established remote connection to PostgreSQL from another machine with another network,
thus function "create_db_and_add_data" will not work if you don't 
have established PostgreSQL server with following properties:

database="unwind_digital_db",
user='postgres',
password='admin',
host='localhost',
port= '5432'

If you have a database with following properties THE CODE DOES WORK and the data will be updated on your local server DB. 

If you have any questions regarding the execution or methods don't hessitate to contact me at denis.ryabich.swi4@gmail.com or denis-ryabich@mail.ru
or conctact me in telegram at https://t.me/Swi4Denis
