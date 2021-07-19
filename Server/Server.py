import re
import socket
import threading
import tkinter as tk
from tkinter import messagebox
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
from fuzzywuzzy import fuzz,process  
import time
import sys
import os

HEADER = 64
HOST = socket.gethostbyname(socket.gethostname())
PORT = 5050
ADDR = (HOST,PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
CLIENT_DISCONNECT_MSG = "Client has disconnected from server." 
LOGIN_MSG_SUCCESS = "Login successful!"
WRONG_PASSWORD = "Login Failed! Username or password is incorrect"
NOT_REGISTERED = "User is not registered!"
ALREADY_LOGGED = "Account has already logged in!"

SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

clients = {}
addresses = {}

#Handle when client crash or disconnect
def client_crash(client):
    if client in clients:
        status_list.insert(tk.END,f"[SERVER] {clients[client]} log out")
        del clients[client]
    else:    
        status_list.insert(tk.END,f"[SERVER] {addresses[client]} disconnected")
   
    del addresses[client]

#Send message to clients
def send(client,msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    try:
        client.send(send_length)
        client.send(message)
    except socket.error:
        raise socket.error

#Receive message from clients
def recv(client): 
    msg = ""
    try:
        msg_length = client.recv(HEADER).decode(FORMAT)
    except socket.error:
        raise socket.error
    else:   
        if msg_length:
            msg_length = int(msg_length)
            msg = client.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                raise socket.error(DISCONNECT_MESSAGE)
        return msg    

#Send message to all connected clients
def broadcast(msg,prefix = ""):
    for sock in clients:
        send(sock,prefix+msg)

#Handle the register process
def register(client,client_address):
    try:    
        username = recv(client)
        password = recv(client)
    except socket.error as e:
        if str(e) == DISCONNECT_MESSAGE:
            client_crash(client)
            return 
    else:
        find_user = ("SELECT * FROM users WHERE username = ?")
        cursor.execute(find_user,[username])
        result = cursor.fetchall()
        
        if result:
            send(client,"Exist")
        else:
            send(client,"Success")
            insert_user = ("""INSERT INTO users (username,password) VALUES (?, ?)""")
            cursor.execute(insert_user,[(username),(password)])
            db.commit()
            status_list.insert(tk.END,f"[SERVER] {username} is sign up successfully")

#Handle the login process
def log_in(client,client_address):
    try:    
        username = recv(client)
        password = recv(client)
    except socket.error as e:
        if str(e) == DISCONNECT_MESSAGE:
            client_crash(client)
            return False
    else:
        find_user = ("SELECT * FROM users WHERE username = ?")
        cursor.execute(find_user,[username])
        result = cursor.fetchall()
        
        if result:
            if result[0][2] == password:
                if client in clients:
                    status_list.insert(tk.END,f"[SERVER] {username} has already logged in")
                    send(client,ALREADY_LOGGED)
                    return True
                else:
                    status_list.insert(tk.END,f"[SERVER] {username} has logged in successfully")
                    send(client,LOGIN_MSG_SUCCESS) 
                    clients[client] = username
                    return False
            else:
                status_list.insert(tk.END,f"[SERVER] {username} logged in failed")
                send(client,WRONG_PASSWORD)
                return True
        else:
            status_list.insert(tk.END,f"[SERVER] {username} is not registered")
            send(client,NOT_REGISTERED)
            return True
            # try:
            #     client_want = recv(client)
            # except socket.error as e:
            #     if str(e) == DISCONNECT_MESSAGE:
            #         client_crash(client)
            #         return False
            # else:
            #     if client_want == "YES":
            #         register(client,client_address) 
            #         return True
            #     else:
            #         return True

#Get the list of golds from third-party
def get_gold_list(date):
    all_golds = {}
    
    #Request to URL and get html data
    URL = f"https://tygia.com/api.php?column=0&cols=1&title=1&chart=0&gold=1&rate=0&expand=2&nganhang=VIETCOM&ngay={date}"
    html_text = requests.get(URL).text
    soup = BeautifulSoup(html_text,"lxml")
    
    #Extract the date of data from html
    present_day = soup.find("span",id = "datepk1")
    
    #Extract the list of information about gold
    list_gold = soup.find_all("tr",class_ = "rmore rmore1")
    SJC_HCM = soup.find("tr",id = "SJCH_Ch_Minh")
    SJC_HN = soup.find("tr",id = "SJCH_N_i")
    list_gold.append(soup.find("tr",id = "SJCH_Ch_Minh"))
    list_gold.append(soup.find("tr",id = "SJCH_N_i"))
    list_gold.append(soup.find("tr", id = "DOJIH_N_iAVPL"))
    list_gold.append(soup.find("tr", id = "DOJIH_Ch_MinhAVPL"))
    list_gold.extend(soup.find_all("tr",class_ = "rmore3"))
    list_gold.extend(soup.find_all("tr",class_ = "rmore4"))
    list_gold.extend(soup.find_all("tr",class_ = "rmore5"))
    #Get the value of the gold consists of name,buy_price,sell_price
    values = []
    for gold in list_gold:
        if gold:
            #Get the gold name
            name = gold.find("td",class_ = "c1 text-left")
            
            #Get the buy tag
            buy = name.find_next("td")
            #Check if the value is available
            if buy.find_all('div'):
                buy_price = buy.div.div.span.text
            else:
                buy_price = "0"
            
            #Get the sell tag
            sell = buy.find_next("td")
            if sell.find_all('div'):
                sell_price = sell.div.div.span.text
            else:
                sell_price = "0"
            name = " ".join(name.text.split())
            
            if gold['id'] != "1OTHERMi_H_ng_950SJC":
                values.append({
                            "name" : name,
                            "buy" : buy_price, 
                            "sell" : sell_price}
                            )
            else:
                values.append({
                            "name" : name,
                            "buy" : sell_price, 
                            "sell" : buy_price}
                            )
    all_golds[present_day.text] = values 
    return all_golds

def create_table_to_gold_database(date):  
    golds = get_gold_list(date)
    
    
    with sqlite3.connect(f'Server Database/Golds.db',check_same_thread = False) as conn:
        cur = conn.cursor()
        for table_name, values in golds.items():
            cur.execute(f"""CREATE TABLE IF NOT EXISTS'{table_name}' (
                    NAME VARCHAR(20) PRIMARY KEY,
                    BUY VARCHAR(20),
                    SELL VARCHAR(20))
                        """)
            for item in values:
                name = item['name']
                buy = item['buy']
                sell = item['sell']
                cur.execute(f"""INSERT INTO '{table_name}' VALUES (?,?,?)""",[name,buy,sell])
            
        conn.commit()
      
def update_datebase_30min_per_day(date = datetime.now()):
    date = date.strftime("%Y%m%d")
    while True:
        with sqlite3.connect(f'Server Database/Golds.db',check_same_thread = False) as conn:
            cur = conn.cursor()    
            golds = get_gold_list(date)
            for table_name, values in golds.items():
                listOfTables = cur.execute(f"""SELECT name FROM sqlite_master WHERE type='table'
                                    AND name='{table_name}';""").fetchall()
                if listOfTables == []:
                    cur.execute(f"""CREATE TABLE '{table_name}'(
                        NAME VARCHAR(20) PRIMARY KEY,
                        BUY VARCHAR(20),
                        SELL VARCHAR(20))
                        """)
                    for value in values:
                        name = value['name']
                        buy = value['buy']
                        sell = value["sell"]
                        cur.execute(f"""INSERT INTO '{table_name}' VALUES(?,?,?)""",[name,buy,sell])
                else:
                    for value in values:
                        name = value['name']
                        buy = value['buy']
                        sell = value["sell"]
                        cur.execute(f"""UPDATE '{table_name}' SET BUY = ?,SELL = ? WHERE NAME = ?""",[buy,sell,name])
            conn.commit()
        min = 30

        time.sleep(min*60)

def query_from_database(name, date):
    results = []
    with sqlite3.connect(f'Server Database/Golds.db',check_same_thread = False) as conn:
        cursor = conn.cursor()
        values = cursor.execute(f"""SELECT * FROM '{date}'""").fetchall()
        if not values:
            return results
        list_of_name = [gold[0] for gold in values]
        the_most_close = process.extractOne(name,list_of_name)
        
        #If the percent larger than 95%
        if the_most_close[1] >= 95:
            values = cursor.execute(f"""SELECT * FROM "{date}" WHERE NAME = ?""",[the_most_close[0]])
            results.extend(values.fetchall())
        else:
            list_of_name = process.extractWithoutOrder(name,list_of_name)
            list_of_name = [item[0] for item in list_of_name if item[1] >= 80]
            
            for name_str in list_of_name:
                cursor.execute(f"""SELECT * FROM "{date}" WHERE NAME = ?""",[name_str])
                results.extend(cursor.fetchall())
                
    return results

def receive_client_query(client):
    try:
        name = recv(client)
        date = recv(client)
    except socket.error:
        client_crash(client)
    else:
        date_format = datetime.strptime(date,"%Y%m%d").strftime("%#d/%#m/%Y")
        with sqlite3.connect(f'Server Database/Golds.db',check_same_thread = False) as conn:
            cur = conn.cursor()
            find_table = cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name= '{date_format}'").fetchall()
        if find_table == []:
            create_table_to_gold_database(date)
        results = query_from_database(name,date_format)
        if results:
            send(client,"FOUND")
            #Send the result to client
            send(client,str(len(results)))
            for item in results:
                send(client,item[0])
                send(client,item[1])
                send(client,item[2])
            send(client,"DONE")
            status_list.insert(tk.END,f"[SERVER] Send results to {clients[client]} successfully")
        else:
            status_list.insert(tk.END,f"[SERVER] Send no results to {clients[client]}")
            send(client,"NOT FOUND")

def send_charts_data(client):
    try:
        name = recv(client)
        date = recv(client)
    except socket.error:
        client_crash(client)
    else:
        date_time = datetime.strptime(date,"%Y%m%d")
        pre_15_day = date_time - timedelta(days=15)
        buy = []
        sell = []
        valid_days = []
        while pre_15_day <= date_time:
            date = pre_15_day.strftime("%Y%m%d")
            date_format = pre_15_day.strftime("%#d/%#m/%Y")
            with sqlite3.connect(f'Server Database/Golds.db',check_same_thread = False) as conn:
                cur = conn.cursor()
                find_table = cur.execute(f"""SELECT name FROM sqlite_master WHERE type='table' AND name= '{date_format}'""").fetchall()
            if find_table == []:
                create_table_to_gold_database(date)
            result = cur.execute(f"SELECT BUY,SELL FROM '{date_format}' WHERE NAME = ?",[name]).fetchall()
            if result:
                valid_days.append(date_format)
                for item in result:
                    buy.append(item[0])
                    sell.append(item[1])
            pre_15_day += timedelta(days=1)
        
        send(client,str(len(valid_days)))
        for item in valid_days:
            send(client,item)
        for item in buy:
            send(client,item)
        for item in sell:
            send(client,item)
        send(client,"DONE")
        
    return 

#Handle client     
def handle_client(client,client_address):
    while True:
        try:
            client_login = recv(client)
        except socket.error as e:
            if str(e) == DISCONNECT_MESSAGE:
                client_crash(client)
                return
        else:
            if client_login == "Login":
                if log_in(client,client_address) == False:
                    break;
            else:
                register(client,client_address)    
    
    connected = True
    while connected:
        try:
            msg = recv(client)
        except socket.error as e:
            if str(e) == DISCONNECT_MESSAGE:
                client_crash(client)
        else:
            if msg == "QUERY":
                status_list.insert(tk.END,f"[SERVER] {clients[client]} just make a search request")
                receive_client_query(client)
            elif msg == "CHART":
                send_charts_data(client)
            else:
                break
    
    client.close()

#Sets up handling for incoming clients.
def accept_incoming_connections():
    while True:
        try:
            client, client_address = SERVER.accept()
        except socket.error:
            break
        else:
            status_list.insert(tk.END,"%s:%s has connected." % client_address)
            addresses[client] = client_address
            threading.Thread(target=handle_client, args=(client,client_address)).start() 

#When closing the server
def on_closing():
    if SERVER.fileno() == -1:
        root.destroy()
        return 
    try:
        if addresses:
            for sock in addresses:
                send(sock,DISCONNECT_MESSAGE)
    except socket.error:
        print(socket.error)
    
    SERVER.close()
    root.destroy()
    sys.exit()
    
    
#Set up database
def setup_database():
    global db,cursor
    
    #Connect to the database
    with sqlite3.connect(f"Server Database/database.db",check_same_thread=False) as db:
        cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            userID INTEGER PRIMARY KEY,
            username VARCHAR(20) NOT NULL,
            password VARCHAR(20) NOT NULL
        )           
    """)

#Start the server
def start_server():
    try:
        SERVER.bind(ADDR)
        SERVER.listen(5)
    except socket.error:
        on_closing()
    else:
        ACCEPT_THREAD = threading.Thread(target=accept_incoming_connections)
        ACCEPT_THREAD.start()

root = tk.Tk()
root.title("SERVER")

DIR = os.getcwd()


if not os.path.exists('Images'):
    messagebox.showerror('Status',"Requirement missing!!!")
    
PATH_IMG = f"{DIR}/Images/"
root.iconbitmap(f"{PATH_IMG}Server.ico")

if not os.path.exists('Server Database'):
    os.makedirs('Server Database')  


app_height = 210
app_width = 621

screen_height = root.winfo_screenheight()
screen_width = root.winfo_screenwidth()

x = (screen_width/2)   - (app_width/2)
y = (screen_height/2)  - (app_height/2)

root.geometry(f"{app_width}x{app_height}+{int(x)}+{int(y)}")

status = tk.StringVar()

messages_frame = tk.Frame(root)
scrollbar = tk.Scrollbar(messages_frame)
status_list = tk.Listbox(messages_frame,width = 100,yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
status_list.pack(side=tk.LEFT, fill=tk.BOTH)
status_list.pack()

messages_frame.pack()

quit_but = tk.Button(root,text = "Quit",command = on_closing)
quit_but.pack(pady = (10,10))
root.protocol("WM_DELETE_WINDOW", on_closing)
        
status_list.insert(tk.END,f"Waiting for connection at {HOST}...")


if __name__ == "__main__":
    setup_database()
    start_server()
    #Start gathering and update data each 30 min on another thread
    threading.Thread(target = update_datebase_30min_per_day,daemon= True).start()
    root.mainloop()


