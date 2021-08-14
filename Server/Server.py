"""Module có sẵn"""
from GetThirdPartyData import ThirdPartyServerData
import socket
import threading
import tkinter as tk
from tkinter import messagebox
import json
import os
import time

"""Module tự viết"""
from ServerDatabase import ServerDatabase
from UI import MainPage
from Constants import *

"""Nếu như file Server Database chưa được tạo thì sẽ tạo thư mục chứa database"""
if os.path.exists("Server Database") == False:
    os.makedirs("Server Database")

"""Đối tượng socket server của chương trình"""
class SocketServer:
    def __init__(self):
        """Khởi tạo"""        
        self.clients = {}
        self.addresses = {}
        self.receive_q = []
    
    """Setter của đối tượng"""
    def set_gui(self,master):
        self.app = master
    
    """Gửi dữ liệu đến client theo format gửi độ dài rồi gửi nội dung"""
    def sendMsg(self,client,msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        try:
            client.send(send_length)
            client.send(message)
        except socket.error:
            raise socket.error
    
    """Hàm gửi 1 list dữ liệu"""
    def sendList(self,client,list_data):
        data = json.dumps(list_data)
        list_len = len(data)
        send_len = str(list_len).encode(FORMAT)
        send_len += b' ' * (HEADER - len(send_len))
        try:
            client.send(send_len)
            client.send(data.encode(FORMAT))
        except socket.error:
            raise socket.error
        
    """Nhận dữ liệu từ client"""
    def receiveMsg(self,client): 
        msg = ""
        try:
            msg_length = client.recv(HEADER).decode(FORMAT)
        except socket.error:
            raise socket.error
        else:   
            try:
                if msg_length:
                    msg_length = int(msg_length)
                    msg = client.recv(msg_length).decode(FORMAT)
            except socket.error:
                raise socket.error
            else:  
                return msg    

    """Hàm nhận 1 list dữ liệu"""
    def receiveList(self,client):
        list_recv = []
        try:
            list_length = client.recv(HEADER).decode("utf-8")
        except socket.error:
            raise socket.error
        else:
            try:
                if list_length:
                    list_recv = client.recv(int(list_length)).decode("utf-8")
                    list_recv = json.loads(list_recv)
            except socket.error:
                raise socket.error
            else:          
                return list_recv
           
    """Tạo socket server"""
    def create_server(self):
        self.SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    """Xử lí yêu cầu người dùng"""    
    def handle_client(self,client):
        last_client_IP = client
        login_status = False
        connected = True
        stop_receive = False
        while connected:
            try:
                """Lắng nghe và gửi thông báo điến client liên tục"""
                if stop_receive == False:
                    self.sendMsg(client,"PACKET")
                    msg = self.receiveMsg(client)
                    
                    if msg == ALREADY_LOGGED:
                        login_status = True
                        self.server_re_online(client)
                    elif msg == "STOP_FROM_CLIENT":
                        """Nếu client có tín hiệu cần gửi thông tin đế server thì dừng quá trình này"""
                        stop_receive = True  
                        self.sendMsg(client,"STOP_FROM_SERVER") 
                    elif msg == DISCONNECT_MESSAGE:
                        self.client_disconnect(client)
                        break
                else:
                    """Trạng thái đăng nhập = False là chưa đăng nhập vào server"""
                    if login_status == False:
                        msg = self.receiveMsg(client)
                       
                        if msg == LOGIN:
                            if self.log_in(client) == True:
                                login_status = True
                        elif msg == SIGN_UP:
                            self.register(client) 
                        elif msg == DISCONNECT_MESSAGE:
                            self.client_disconnect(client)
                            connected = False
                        stop_receive = False
                    else:
                        """Đăng nhập thành công thì client mới có quyền tra cứu"""
                        msg = self.receiveMsg(client)
                        if msg == QUERY:
                            self.receive_client_query(client)
                        elif msg == CHART:
                            self.send_charts_data(client)
                        elif msg == DISCONNECT_MESSAGE:
                            self.client_log_out(client)
                            connected = False
                        stop_receive = False
                       
            except socket.error:
                """Trong quá trình truyền nếu client bị mất kết nối đột ngột """
                """thì xoá client đó bắt client đó kết nối lại"""
                self.client_crash(last_client_IP)
                
                connected = False #Phá vòng lập không còn kết nối nữa  
                break
           
            """Tín hiệu để phá vòng lập và gửi thông báo server ngừng kết nối đến các client"""
            """Lấy từ đối tượng UI khi người dùng ấn quit"""
            if self.app.get_disconnect_flag():
                break
        
        """Khi mà server còn đang kết nối đến client thì gửi tín hiệu ngừng kết nối"""
        if connected:
            self.sendMsg(client,DISCONNECT_MESSAGE)
        
    """Chờ các client khác kết nối"""
    def accept_incoming_connections(self):
        """Luôn lặp lại"""
        while True:
            try:
                """Chấp nhận 1 kết nối từ client"""
                client, client_address = self.SERVER.accept()
            except socket.error:
                """Nếu client đó kết nối bị lỗi thì thử lại"""
                continue
            else:
                """Client kết nối thành công"""
                self.app.insert_to_text_box(f"[SERVER] {client_address} has connected.")
                
                """Lưu địa chỉ vào biến"""
                self.addresses[client] = client_address
                
                """Bắt đầu luồng để xử lí yêu cầu của client"""
                threading.Thread(target=self.handle_client, args=(client,)).start() 
    
    """Chạy server"""
    def start_server(self):
        self.create_server()
        try:
            self.SERVER.bind(ADDR) #Bind server trên địa chỉ ADDR 
            self.SERVER.listen(5)
        except socket.error:
            """Nếu không mở được server thì trả về lỗi rồi đóng server ngay lập tức"""
            messagebox.showerror("Error","  Can't start server")
            os._exit(1)
        else:
            """Mở server thành công thì sẽ mở luồng đợi các kết nối của client"""
            self.app.insert_to_text_box(f"Waiting for connection at {HOST}...")
           
            """Luồng đợi các kết nối từ client"""
            ACCEPT_THREAD = threading.Thread(target=self.accept_incoming_connections)
            ACCEPT_THREAD.start()
    
    """Người dùng đăng kí"""
    def register(self,client):
        try:    
            info = self.receiveList(client)
            username = info[0]
            password = info[1]
        
            """Kiểm tra xem trong database có dữ liệu người dùng hay chưa"""
            result = ServerDatabase.find_user_info(username)
            
            if result:
                """Nếu có thì đăng kí thất bại"""
                self.sendMsg(client,ALREADY_EXIT)
                self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} sign up failed")
            else:
                """Nếu không tồn tại thì đăng kí thành công"""
                self.sendMsg(client,SIGN_UP_SUCCESS)
                self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} sign up successfully")
                
                """Lưu vào database"""
                ServerDatabase.insert_user(username,password)
        except socket.error:
            raise socket.error
        
    """Người dùng đăng nhập"""
    def log_in(self,client):
        try:    
            info = self.receiveList(client)
            username = info[0]
            password = info[1]
      
            """Tìm người dùng trong cơ sở dữ liệu"""
            result = ServerDatabase.find_user_info(username)
            
            """Nếu tìm thấy"""
            if result:
                """Kiểm tra mật khẩu có đúng hay không"""
                if result[0][2] == password:
                    """Nếu đúng thì kiểm tra xem người dùng đã đăng nhập hay chưa"""
                    
                    if self.clients:    
                        for key,user in self.clients.items():
                            if user == username:
                                """Nếu đăng nhập rồi thì trả về False kèm thông báo"""
                                self.app.insert_to_text_box(f"[SERVER] {username} has already logged in")
                                self.sendMsg(client,ALREADY_LOGGED)
                                return False
                            else:
                                """Nếu chưa đăng nhập và mật khẩu đúng thì trả về True kèm thông báo"""
                                self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} has logged in successfully")
                                self.app.insert_to_text_box(f"[SERVER] {username} - Welcome to Server")
                                self.sendMsg(client,LOGIN_MSG_SUCCESS)
                                self.send_name_of_golds(client)
                                self.clients[client] = username
                                return True
                    else:
                        """Nếu chưa có người dùng nào đăng nhập và mật khẩu đúng thì trả về True kèm thông báo"""
                        self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} has logged in successfully")
                        self.app.insert_to_text_box(f"[SERVER] {username} - Welcome to Server")
                        self.sendMsg(client,LOGIN_MSG_SUCCESS) 
                        self.send_name_of_golds(client)
                        self.clients[client] = username
                        return True
                else:
                    """Nếu mật khẩu sai thì trả về False kèm thông báo"""
                    self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} logged in failed")
                    self.sendMsg(client,WRONG_PASSWORD)
                    return False
            else:
                """Nếu chưa đăng ký thì trả về False kèm thông báo"""
                self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} logged in failed")
                self.sendMsg(client,NOT_SIGN_UP)
                return False
        except socket.error:
            raise socket.error


    """Người dùng tra giá vàng"""
    def receive_client_query(self,client):
        try:
            self.app.insert_to_text_box(f"[SERVER] {self.clients[client]} just make a search request")
            info = self.receiveList(client)
            name = info[0]
            date = info[1]
            
            results = ServerDatabase.query_from_database(name,date)
              
            if results:
                self.last_query_date = date
                self.sendMsg(client,FOUND)
                self.sendList(client,results)
                self.sendMsg(client,DONE)
                self.app.insert_to_text_box(f"[SERVER] Send results to {self.clients[client]} successfully")
            else:
                self.app.insert_to_text_box(f"[SERVER] Send no results to {self.clients[client]}")
                self.sendMsg(client,NOT_FOUND)
        except socket.error:
            raise socket.error
    
    """Gửi dữ liệu của đồ thị qua cho client"""
    def send_charts_data(self,client):
        try:
            info = self.receiveList(client)
            name = info[0]
            date = info[1]
            results = ServerDatabase.query_from_database_15_days_before(name,date)
            if results:
                self.sendMsg(client,FOUND)
                self.sendList(client,results)
                self.sendMsg(client,DONE)
            else:
                self.sendMsg(client,NOT_FOUND)
        except socket.error:
            raise socket.error
    
    """Gửi list tên các loại vàng"""
    def send_name_of_golds(self,client): 
        try:
            list_name = ServerDatabase.get_name_of_golds()
            if not list_name:
                self.sendMsg(client,NOT_FOUND)
            else:
                self.sendMsg(client,FOUND)
                self.sendList(client,list_name)
        except socket.error:
            raise socket.error        
    """Client ngắt kết nối chưa đăng nhập"""
    def client_disconnect(self,client):
        self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} disconnected")
        
        """Xoá địa chỉ IP đã kết nối đến server"""
        del self.addresses[client]
        
        """Đóng kết nối"""
        client.close()

    """Client đăng xuất"""
    def client_log_out(self,client):
        """Client muốn đóng kết nối khi đã đăng nhập"""
        self.app.insert_to_text_box(f"[SERVER] {self.clients[client]} log out")
        
        """Xoá thông tin người dùng và địa chỉ IP khỏi server"""
        del self.clients[client]
        del self.addresses[client]
        
        """Đóng socket client"""
        client.close()
        
    """Khi client đột ngột tắt"""
    def client_crash(self,client):
        """Nếu client đã đăng nhập thì xoá client trong biến các người dùng đã đăng nhập"""
        if client in self.clients:
            self.app.insert_to_text_box(f"[SERVER] User {self.clients[client]} crash ")
            del self.clients[client]
        else:
            """Chưa đăng nhập thì coi như 1 địa chỉ IP bình thường bị mất kết nối"""
            self.app.insert_to_text_box(f"[SERVER] {self.addresses[client]} crash ")
        """Xoá thông tin socket client"""
        del self.addresses[client]  
        
        """Đóng socket trên đỉa chỉ IP đó"""
        client.close() 
    
    """Server vừa mới mở lại sau khi bị crash"""
    """Cập nhật các thông tin client đã kết nối trước đó"""
    def server_re_online(self,client):
        try:
            username = self.receiveMsg(client)
            self.app.insert_to_text_box(f"[SERVER] {username} - Welcome back to Server")
            self.clients[client] = username
        except socket.error:
            raise socket.error  

"""Chương trình socket server"""
class ServerApplication():
    def __init__(self,master):
        """Khởi tạo đối tượng"""
        self.root = master
        self.root.resizable(False,False)
        self.main_page = MainPage(self.root)
        self.database = ServerDatabase()
        self.server = SocketServer()
        self.server.set_gui(self.main_page)
        self.server.start_server()
      
if __name__ == "__main__":
    root = tk.Tk()
    app = ServerApplication(root)
    root.mainloop()


