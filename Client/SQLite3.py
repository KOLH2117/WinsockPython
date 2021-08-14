import sqlite3
from PIL import ImageTk, Image
import os
DIR = os.path.dirname(__file__)
print(DIR)
def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData

def insertBLOB(name, photo):
    try:
        sqliteConnection = sqlite3.connect(DIR +"/Database.db")
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")
        sqlite_insert_blob_query = """ INSERT INTO 'Images'
                                  (Name, Photo) VALUES (?, ?)"""

        empPhoto = convertToBinaryData(photo)
        data_tuple = (name, empPhoto)
        cursor.execute(sqlite_insert_blob_query, data_tuple)
        sqliteConnection.commit()
        print("Image and file inserted successfully as a BLOB into a table")
        cursor.close()

    except sqlite3.Error as error:
        print("Failed to insert blob data into sqlite table", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()
            print("the sqlite connection is closed")

def extract_picture(name):
    sqliteConnection = sqlite3.connect(DIR +"/Database.db")
    cursor = sqliteConnection.cursor()
    sql = """SELECT Photo FROM Images WHERE id = 1 AND Name = ?"""
    param = (name)
    cursor.execute(sql, param)
    result = cursor.fetchone()
    print (result)
    # filename = afile + ext
    # with open(filename, 'wb') as output_file:
    #     output_file.write(ablob)
    # return filename
# with sqlite3.connect(DIR +"/Database.db",check_same_thread= False) as db: 
#     cur = db.cursor()
#     sql_img = """CREATE TABLE Images (
#             ID INTEGER PRIMARY KEY AUTOINCREMENT, 
#             Name TEXT NOT NULL, 
#             Photo BLOB NOT NULL)"""
#     cur.execute(sql_img)
    
    
#     db.commit()
# insertBLOB("GOLD_IMG","Images/Gold_img.png")
extract_picture("GOLD_IMG")
