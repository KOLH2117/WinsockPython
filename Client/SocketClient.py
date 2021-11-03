"""Module bổ trợ"""
import re
import threading
import time
from tkinter import messagebox
import json

"""Module socket với các module tự viết"""
import socket
from Constants import *
from UI import LoadingScreen 

class SocketClient:
    def __init__(self):
        """List bổ trợ"""
        self.send_q = [] # List lưu yêu cầu của client
        self.list_name_of_golds = [] # Lưu tên các loại vàng từ server
        
        """Cờ hiệu"""
        self.login_status = False # Tình trạng đăng nhập của client
        self.disconnect_flag = False # Cờ client bật lên client ngắt kết nối
        self.listen = True # Lắng nghe từ server
        
        """Lưu dữ liệu tra cuối lần cuối cùng"""
        self.last_username = None # Tên tài khoản đã đăng nhập vào server
        self.last_query_date = None # Ngày tra cuối cùng của client
    
    """Hàm setter và getter của đối tượng"""
    """Hàm để lấy ứng dụng để thay đổi GUI"""
    def set_app(self,app):
        self.app = app    
        self.set_GUI(app.root)
     
    def set_GUI(self,master):
        self.master = master
        
    def get_name_of_golds(self):
        return self.list_name_of_golds
    
    """Tạo đối tượng socket"""    
    def create_socket(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    """Đóng socket"""
    def close_client(self):
        self.client.close()

    """Client ngắt kết nối"""
    def client_disconnect(self):
        self.exit =  LoadingScreen(self.master)   
        try:
            """Kiểm tra xem client đã đóng kết nối với server hay chưa"""
            if self.client.fileno() != -1:
                self.disconnect_flag = True
                self.add_message(DISCONNECT_MESSAGE)
                time.sleep(1)
                self.send(DISCONNECT_MESSAGE)
                self.remove_message()
        finally: 
            time.sleep(2)
            self.client.close()
            self.exit.stop()
            self.exit.master_exit()
                
    """Client đang kết nối lại đến server"""
    def client_try_to_reconnect(self):
        loading = LoadingScreen(self.master,text= "Đang kết nối lại...")
        """Đóng rồi tạo lại socket"""
        self.close_client()
        
        """5 lần thử"""
        for i in range(5):
            self.create_socket()
            
            try:
                self.client.settimeout(3)
                self.client.connect(self.ADDR)
                self.client.settimeout(None) 
            except socket.error as e:
                """Nếu lỗi thì đóng rồi thử lại trên 1 socket khác"""
                self.close_client()
                """Nghỉ 2s rồi thử lại"""
                time.sleep(1.5)
            else:
                loading.stop()
                """Kết nối lại thành công trả về True"""
                return True  
        else:
            """Không thành công trả về False""" 
            loading.stop()   
            return False 
    
    """Bắt đầu kết nối đến Server"""
    def start_connections(self,HOST_IP):     
        self.HOST = HOST_IP
        self.PORT = 5050
        self.ADDR = (self.HOST,self.PORT)
        
        self.create_socket()
        try:
            self.client.settimeout(3) 
            self.client.connect(self.ADDR) 
            self.client.settimeout(None)             
        except socket.error as e:
            self.close_client()
            return False
        else:
            """Luồng lắng nghe và gửi yêu cầu đến server"""
            t = threading.Thread(target=self.listen_from_server)
            t.setDaemon(True)
            t.start()
            return True            
    
    """Lắng nghe từ server"""
    def listen_from_server(self):
        """Luôn luôn lắng nghe ở backend"""
        user_reconnect = False
        flag = True
        while flag:
            """Kiểm tra xem client có dừng kết nối hay không: True là dừng False là không dừng"""
            if self.disconnect_flag == True:
                break
            """Vòng lặp để lắng nghe từ server"""
            while self.listen:
                try:
                    ack_msg = "ACK"
                    """Nhận PACKET từ Server"""
                    msg = self.receive()
                    
                    if msg == DISCONNECT_MESSAGE:
                        """Nếu Server gửi thông báo ngừng kết nối thì Client sẽ nhận được và tắt chương trình"""
                        messagebox.showwarning("Trạng thái", "Server sẽ ngắt kết nối")
                        self.server_shutdown()
                        
                        """Phá vòng lặp lớn bên ngoài"""
                        flag = False
                        break
                    """Kiểm tra lần cuối đã đăng nhập hay chưa"""
                    """Nếu chưa thì bỏ qua"""
                    """Nếu đã đăng nhập thì gửi thông báo cho Server biết và tài khoản"""
                    if self.login_status == True and user_reconnect == True:
                        self.send(ALREADY_LOGGED)
                        self.send(self.last_username)    
                        user_reconnect = False
                        continue
                    """Khi mà client có yêu cầu gửi đến Server"""
                    """Sẽ thêm yếu cầu vào 1 list"""
                    """Nếu list đó có dữ liêu thì client ngừng nghe mà bắt đầu gửi yếu cầu"""
                    if len(self.send_q) != 0:
                        """Đây là thông báo cho Server biết là hãy dừng gửi PACKET và nghe yêu cầu"""
                        ack_msg = "STOP_FROM_CLIENT"
                    
                    """Sau khi gửi thông báo STOP_FROM_CLIENT"""
                    """Sẽ nhận lại thông báo từ Server là họ đã nhận được yêu cầu dừng gửi PACKET và lắng nghe yêu cầu của client"""
                    if msg == "STOP_FROM_SERVER":
                        """Set cờ lắng nghe bằng False không cho nghe nữa"""
                        self.listen = False
                        """Phá vòng lặp nghe"""
                        break
                    """Nếu không có yêu cầu từ client thì client sẽ gửi lại 1 ACK"""
                    """Nếu có yêu cầu từ client thì client gửi trả STOP_FROM_CLIENT"""
                    self.send(ack_msg)  
                
                except socket.error:
                    """Nếu có lỗi trong quá trình chuyền nhận vd như server đột ngột tắt"""
                    """Đến hàm server_crash"""
                    if self.server_crash() == False:
                        """False là không kết nối lại được đến Server"""
                        messagebox.showinfo("Trạng thái", "Không thể kết nối lại với Server")
                        self.close_client()
                        self.app.reset()
                        return                 
                    else:
                        """Kết nối lại đến Server thành công"""
                        if self.login_status == False:
                            user_reconnect = False
                        else:
                            user_reconnect = True
    
    """Thêm yêu cầu"""
    def add_message(self, msg):
        self.send_q.append(msg)

    """Xoá yêu cầu"""
    def remove_message(self):
        self.send_q.pop(0)
        if len(self.send_q) == 0:
            self.listen = True

    """Hàm gửi 1 thông báo đến server"""
    def send(self,msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        try:
            self.client.send(send_length)
            self.client.send(message)
        except socket.error as e:
            raise socket.error
        
    """Hàm gửi 1 list dữ liệu"""
    def sendList(self,list_data):
        data = json.dumps(list_data)
        list_len = len(data)
        send_len = str(list_len).encode(FORMAT)
        send_len += b' ' * (HEADER - len(send_len))
        try:
            self.client.send(send_len)
            self.client.send(data.encode(FORMAT))
        except socket.error:
            raise socket.error
    
    """Hàm nhận 1 thông báo từ server"""  
    def receive(self):
        msg = ""
        try:
            msg_length = self.client.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg = self.client.recv(int(msg_length)).decode(FORMAT) 
        except socket.error:
            raise socket.error
        else:
            return msg 

    """Hàm nhận 1 list dữ liệu"""
    def receiveList(self):
        list_recv = []
        try:
            list_length = self.client.recv(HEADER).decode("utf-8") 
            if list_length:
                list_recv = self.client.recv(int(list_length)).decode("utf-8")
                if list_recv:
                    list_recv = json.loads(list_recv)
        except socket.error:
            raise socket.error
        else:
            return list_recv
                
    """Xử lí đăng ký"""
    def register(self,username, password):   
        try:
            self.add_message(SIGN_UP)
            while True: 
                if self.listen == False:
                    self.send(SIGN_UP)
                    self.sendList((username, password))
                    sign_up_msg = self.receive()
                    break
        except socket.error:
            self.remove_message()  
            return ERROR
        else:  
            self.remove_message()  
            return sign_up_msg

    """Xử lý đăng nhập"""
    def login(self,username, password):
        try:
            self.last_username = username
            self.add_message(LOGIN)
            """Đợi cờ lắng nghe về False"""
            while True: 
                if self.listen == False:
                    """Gửi thông tin đăng nhập"""
                    self.send(LOGIN)
                    self.sendList((username, password))
                    
                    """Nhận kết quả từ server"""
                    login_msg = self.receive()
                    if login_msg == LOGIN_MSG_SUCCESS:
                        self.login_status = True
                        """Nhận 1 list tên vàng các loại"""
                        msg = self.receive()
                        if msg != NOT_FOUND:
                            self.list_name_of_golds = self.receiveList()
                    else:
                        self.login_status = False
                    break
        except socket.error as e:
            self.remove_message()  
            return ERROR
        else:
            self.remove_message()  
            return login_msg
            
    """Xử lý tra cứu giá vàng"""
    def start_query_from_server(self,name,date):
        self.last_query_date = date
        list_gold = []
        
        self.add_message(QUERY)
        
        while True: 
            if self.listen == False:
                try:
                    self.send(QUERY)
                    self.sendList((name,date.strftime("%Y%m%d")))
                    
                    msg = self.receive()
                    if msg == FOUND:
                        list_gold = self.receiveList()
                        msg = self.receive()
                        
                except socket.error as e:
                    self.remove_message() 
                    return ERROR,None
                else:
                    self.remove_message() 
                    return msg,list_gold
    
    """Lấy dữ liệu cho đồ thị giá vàng(optional không có trong đề bài)"""    
    def get_chart_value_from_server(self,name):   
        date = self.last_query_date
        result = []
        self.add_message(CHART)
        while True:
            if self.listen == False:
                try:
                    """Gửi yêu cầu và thông tin đến server"""
                    self.send(CHART)
                    self.sendList((name,date.strftime("%Y%m%d")))
                    
                    status = self.receive()
                    if status == FOUND:
                        """Nhận dữ liệu từ server"""
                        result = self.receiveList()
                        
                        """Nhận phản hồi từ server""" 
                        msg = self.receive()  
                    else:
                        msg = NOT_FOUND
                except socket.error:
                    self.remove_message()
                    return ERROR,result
                else:
                    self.remove_message()
                    return msg,result

    """Hàm xử lý khi server dừng kết nối (shut down)"""  
    def server_shutdown(self):
        self.close_client()
        loading = LoadingScreen(self.master)
        time.sleep(2)
        loading.stop()
        loading.master_exit()   

    """Hàm khi Server bị crash"""
    def server_crash(self):
        """Hỏi người dùng xem có muốn kết nối lại hay không"""
        reconnect = messagebox.askretrycancel("Trạng thái","Server bị crash\nKết nối lại???")
        if reconnect == False:
            """Nếu không thì tắt chương trình"""
            self.client_disconnect()
            return False
        else:
            """Nếu có thì thử kết nối lại"""
            if self.client_try_to_reconnect() == True:
                return True
            else:
                return False       

   