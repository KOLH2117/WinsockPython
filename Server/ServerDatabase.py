import sqlite3
import threading
import time
from datetime import datetime,timedelta
from fuzzywuzzy import process
from GetThirdPartyData import ThirdPartyServerData
from requests import exceptions
from tkinter import messagebox
import os

USER_DATABASE_PATH =  "Server Database\Database.db"
GOLDS_DATABASE_PATH =  "Server Database\Golds.db"

class ServerDatabase:
    def __init__(self):
        self.setup_database()
        threading.Thread(target = self.update_datebase_30min_per_day,daemon = True).start()

    """Chuẩn bị cơ sở dữ liệu"""
    def setup_database(self):
        """Kết nối đến database"""
        try:
            with sqlite3.connect(USER_DATABASE_PATH,check_same_thread=False) as conn:
                cursor = conn.cursor()
                
                """Tạo bảng dữ liệu người dùng nếu chưa tồn tại"""
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        userID INTEGER PRIMARY KEY,
                        username VARCHAR(20) NOT NULL,
                        password VARCHAR(20) NOT NULL
                    )           
                """)
                
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Error",e)
            os._exit(1)
    
    """Hàm tìm dữ liệu người dùng trong cơ sở dữ liệu"""
    def find_user_info(username):
        with sqlite3.connect(USER_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()
            find_user = ("SELECT * FROM users WHERE username = ?")
            cursor.execute(find_user,[username])
            result =  cursor.fetchall() 
        
        return result

    """Hàm nhập dữ liệu người dùng vào cơ sở dữ liệu"""
    def insert_user(username,password):
        with sqlite3.connect(USER_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()
            insert_user = ("""INSERT INTO users (username,password) VALUES (?, ?)""")
            cursor.execute(insert_user,[(username),(password)])
            conn.commit()
            
    """Hàm cập nhật dữ liệu từ third party 30 phút 1 lần"""
    def update_datebase_30min_per_day(self,date = datetime.now()):
        date = date.strftime("%Y%m%d")
        while True:  
            """Lấy dữ liệu từ third party về"""
            try:
                golds = ThirdPartyServerData.get_gold_list(date)
            except exceptions.ConnectionError:
                continue
            except exceptions.Timeout:
                continue
            
            try:
                with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
                    cursor = conn.cursor()  
                    for table_name, values in golds.items():
                        listOfTables = cursor.execute(f"""SELECT name FROM sqlite_master WHERE type='table'
                                            AND name= '{table_name}';""").fetchall()
                        if listOfTables == []:
                            cursor.execute(f"""CREATE TABLE '{table_name}'(
                                NAME VARCHAR(20) PRIMARY KEY,
                                BUY VARCHAR(20),
                                SELL VARCHAR(20))
                                """)
                        
                            for value in values:
                                name = value['name']
                                buy = value['buy']
                                sell = value["sell"]
                                cursor.execute(f"""INSERT INTO '{table_name}' VALUES(?,?,?)""",[name,buy,sell])
                        else:
                            for value in values:
                                name = value['name']
                                buy = value['buy']
                                sell = value["sell"]
                                cursor.execute(f"""UPDATE '{table_name}' SET BUY = ?,SELL = ? WHERE NAME = ?""",[buy,sell,name])
                    conn.commit()
            except sqlite3.Error as e:
                messagebox.showerror("Error",e)
                os._exit(1)
            min = 30
            time.sleep(min*60)

    """Hàm tìm dữ liệu giá vàng trong database tìm gần đúng tên"""
    def find_approximate_from_database(name, date):
        if ServerDatabase.check_gold_table_exists(date) == False:
            return None
        
        results = []
        with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()
            values = cursor.execute(f"""SELECT * FROM '{date}'""").fetchall() 
            if not values:
                return results
            list_of_name = [gold[0] for gold in values] 
            """Tìm tên gần đúng nhất với tên người dùng đang tìm"""
            the_most_close = process.extractOne(name,list_of_name)
            
            """Nếu độ chính xác hơn 95% thì trả về giá vàng của loại đó"""
            if the_most_close[1] >= 95:
                values = cursor.execute(f"""SELECT * FROM "{date}" WHERE NAME = ?""",[the_most_close[0]])
                results.extend(values.fetchall())
            else:
                """Nếu độ chính xác bé hơn 95% thì trả về 1 danh sách giá vàng của các loại gần đúng với độ chính xác hơn 80%"""
                list_of_name = process.extractWithoutOrder(name,list_of_name)
                list_of_name = [item[0] for item in list_of_name if item[1] >= 80]
                
                """Lấy dữ liệu từ danh sách kêt quả tên ở trên"""
                for name_str in list_of_name:
                    cursor.execute(f"""SELECT * FROM "{date}" WHERE NAME = ?""",[name_str])
                    results.extend(cursor.fetchall())
                    
        return results

    """Hàm tạo bảng dữ liệu"""
    def create_table_in_gold_database(date):  

        try:
            golds = ThirdPartyServerData.get_gold_list(date)
        except exceptions.ConnectionError:
            return False
        except exceptions.Timeout:
            return False
        
        if golds == None:
            return False
        
        with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()
            for table_name, values in golds.items():
                cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{table_name}' (
                        NAME VARCHAR(20) PRIMARY KEY,
                        BUY VARCHAR(20),
                        SELL VARCHAR(20))
                            """)
                for item in values:
                    name = item['name']
                    buy = item['buy']
                    sell = item['sell']
                    cursor.execute(f"""INSERT INTO '{table_name}' VALUES (?,?,?)""",[name,buy,sell])
                
            conn.commit()
            return True
    
    """Tìm từ database"""    
    def query_from_database(name,date):
        date_format = datetime.strptime(date,"%Y%m%d").strftime("%#d/%#m/%Y")
        if ServerDatabase.check_gold_table_exists(date_format) == False:
            if ServerDatabase.create_table_in_gold_database(date) == False:
                return None
        results =  ServerDatabase.find_approximate_from_database(name,date_format)
        return results
    
    """Kiểm tra xem bảng đã có trong database hay chưa"""
    def check_gold_table_exists(table_name):
        with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
            cur = conn.cursor()
            find_table = cur.execute(f"""SELECT name FROM sqlite_master WHERE type='table' AND name= '{table_name}'""").fetchall()
        if find_table == []:
            return False
        return True
    
    """Tìm dữ liệu cách 15 ngày từ ngày tra"""
    def query_from_database_15_days_before(name,date):
        date_time = datetime.strptime(date,"%Y%m%d")
        pre_15_day = date_time - timedelta(days=15)
        list_results = []
        while pre_15_day <= date_time:
            date = pre_15_day.strftime("%Y%m%d")
            date_format = pre_15_day.strftime("%#d/%#m/%Y")
            if ServerDatabase.check_gold_table_exists(date_format) == False:
                if ServerDatabase.create_table_in_gold_database(date) == False:
                    pre_15_day += timedelta(days=1)
                    continue
            result = ServerDatabase.find_approximate_from_database(name,date_format)
            if result:
                list_results.append((date_format,result[0][1],result[0][2]))
                
            pre_15_day += timedelta(days=1)
        
        return list_results

    """Lấy list tên vàng từ database"""
    def get_name_of_golds(date = datetime.now()):
        date = date.strftime("%#d/%#m/%Y")
        with sqlite3.connect(GOLDS_DATABASE_PATH,check_same_thread = False) as conn:
            cursor = conn.cursor()   
            list_of_name = cursor.execute(f"SELECT NAME FROM '{date}' ORDER BY rowid").fetchall()
            list_of_name = [name[0] for name in list_of_name]
            return list_of_name 
        
  
               