"""Module hỗ trợ backend"""
import re
import os
import sys
import threading
import time
from datetime import datetime
from fuzzywuzzy import process

"""Module hỗ trợ frontend"""
import tkinter as tk
from ctypes import windll
from tkcalendar import Calendar, DateEntry
from tkinter import messagebox, ttk
from PIL import ImageTk, Image

"""Module hỗ trợ vẽ đồ thị"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick 

"""Module chứa các hằng số"""
from Constants import *

"""Lấy ảnh của chương trình"""
class AppImage:
    def __init__(self):
        return
    
    def get(name):
        if name in IMG_LIST:
            if IMG_LIST[name][1] is None:
                if name == "GOLD_IMG":
                    img = Image.open(f"{PATH_IMG}Gold_img.png")
                    img = img.resize((100, 100))
                    IMG_LIST[name][1] = ImageTk.PhotoImage(img)
                else:
                    IMG_LIST[name][1] = ImageTk.PhotoImage(file=IMG_LIST[name][0])
                return IMG_LIST[name][1]
            else:
                return IMG_LIST[name][1]
        return None

"""Căn chỉnh chương trình"""
class JustifyApp:
    """Hàm căn giữa chỉnh màn hình"""
    def center(master, app_width, app_height):
        SCREEN_HEIGHT = master.winfo_screenheight()
        SCREEN_WIDTH = master.winfo_screenwidth()

        x = (SCREEN_WIDTH/2) - (app_width/2)
        y = (SCREEN_HEIGHT/2) - (app_height/2)

        master.geometry(f"{app_width}x{app_height}+{int(x)}+{int(y)}")

"""Hàm bổ trợ"""
class Tk(tk.Tk):
    """Hàm di chuyển màn hình"""
    lastClickX = 0
    lastClickY = 0
    def move_window(self):
        """Nguồn: https://stackoverflow.com/questions/63217105/tkinter-overridedirect-minimizing-and-windows-task-bar-issues"""
        def SaveLastClickPos(event):
            global lastClickX, lastClickY
            lastClickX = event.x
            lastClickY = event.y
          
        def Dragging(event):
            x, y = event.x - lastClickX + self.winfo_x(), event.y - lastClickY + self.winfo_y()
            self.geometry("+%s+%s" % (x, y))

        self.bind('<Button-1>', SaveLastClickPos)
        self.bind('<B1-Motion>', Dragging)
    
    """Hàm để bôi đen được chữ trong ô nhập"""
    def select_entry(self,root):
        self.bind('<ButtonPress-1>',lambda event : root.unbind('<B1-Motion>'))
        self.bind('<ButtonRelease-1>',lambda event : Tk.move_window(root))
    
    """Hàm xoá thanh title của chương trình"""
    def set_appwindow(self):
        """Nguồn: https://stackoverflow.com/questions/63217105/tkinter-overridedirect-minimizing-and-windows-task-bar-issues"""
        GWL_EXSTYLE = -20
        WS_EX_APPWINDOW = 0x00040000
        WS_EX_TOOLWINDOW = 0x00000080
        hwnd = windll.user32.GetParent(self.winfo_id())
        style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style = style & ~WS_EX_TOOLWINDOW
        style = style | WS_EX_APPWINDOW
        res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        self.wm_withdraw()
        self.after(10, lambda: self.wm_deiconify())

    """Xoá màn hình app"""
    def clear_frame(self):
        for widget in self.winfo_children():
            widget.destroy()

"""Thanh chờ tải của chương trình"""
class LoadingScreen():
    """Nguồn tham khảo: https://www.youtube.com/watch?v=nl0mePCxoGU&t=1s"""
    def __init__(self,master,*args,**kwargs):
        master.withdraw()
        if "time_live" in kwargs:
            self.time_live = kwargs.get("time_live")
        else:
            self.time_live = 5
        if "x" in kwargs:
            self.info_x = kwargs.get("x")
        else:
            self.info_x = 100
        if "y" in kwargs:
            self.info_y = kwargs.get("y")
        else:
            self.info_y = 35
        if "text" in kwargs:
            self.text = kwargs.get("text")
        else:
            self.text = "Đang shut down..."
            
        self.root = tk.Toplevel(master)
        self.master = master
        self.stop_flag = False
        self.app_width = 350
        self.app_height = 80
        self.root.resizable(False, False)
        """Căn thanh loading giữa màn hình"""
        JustifyApp.center(self.root,self.app_width,self.app_height)
        self.root.wm_attributes("-transparentcolor",self.root["bg"])
        self.root.overrideredirect(1)
        
        self.frame = tk.Frame(self.root,width = 1000,height = 28)
        self.frame.place(x = self.info_x,y = self.info_y )
        self.Info_label = tk.Label(self.frame,text= self.text,fg = "#3a7ff6",font= "Bahnschrift 13")
        self.Info_label.place(x = 0,y=0)
        self.list_label = []
        for i in range(16):
            self.list_label.append(tk.Label(self.root,bg ="#000",width = 2, height = 1))
            self.list_label[i].place(x =(i)*22,y = 10)

        self.root.update()
        self.thread = threading.Thread(target =self.play_animation)
        self.thread.setDaemon(True)
        self.thread.start()
        self.root.after(20, self.check_thread)
    
    def play_animation(self):
        while not self.stop_flag:
            for j in range(16):
                self.list_label[j].config(bg = "#3a7ff6")
                time.sleep(0.06)
                self.root.update_idletasks()
                self.list_label[j].config(bg = "#000")

        for j in range(16):
            self.list_label[j].config(bg = "#3a7ff6")
            time.sleep(0.06)
            self.root.update_idletasks()
                
    def check_thread(self):
        if self.thread.is_alive():
            self.root.after(20, self.check_thread)
        else:
            self.root.destroy()  
            self.master.deiconify()
    
    def stop(self):
        self.stop_flag = True
        
    def master_exit(self):
        os._exit(1)

"""Form để tra giá vàng"""
class QueryGoldForm:
    def __init__(self,app):
        """Xoá màn hình cũ đi"""
        Tk.clear_frame(app.root)
        
        """Khởi tạo"""
        self.app = app
        self.root = app.root
        self.client = app.client
        
        """Cờ hiệu"""
        self.status = None
        self.flag = 0
        
        """Đây là list gợi ý cho người dùng có thể tìm kiếm"""
        """Trích xuất từ server, nêu server trả về rỗng thì sẽ có 1 list tên mặc định"""
        self.list_name = self.client.get_name_of_golds()
        if self.list_name is None:
            """Nếu không lấy được tên từ third party thì lấy tến cố định"""
            self.list_name = [
                    "SJC Long Xuyên",	
                    "SJC HCM",	
                    "SJC Hà Nội",	
                    "SJC Đà Nẵng",	
                    "SJC Nha Trang",	
                    "SJC Cà Mau",
                    "SJC Biên Hòa",	
                    "SJC Miền Tây",	
                    "SJC Quãng Ngãi",	
                    "SJC Bạc Liêu",	
                    "SJC Bình Phước",	
                    "SJC Quy Nhơn",	
                    "SJC Phan Rang",
                    "SJC Hạ Long",
                    "SJC Quảng Nam",
                    "SJC Huế",
                    "DOJI AVPL / Hà Nội",	
                    "DOJI AVPL / HCM",
                    "VIETINBANK GOLD",
                    "SCB",
                    "MARITIME BANK",
                    "SACOMBANK",
                    "Mi Hồng SJC",
                    "PHÚ QUÝ SJC",
                    "PNJ SJC",
                    "PNJ 1L",
                    "Nhẫn PHÚ QUÝ 24K",	
                    "Mi Hồng 999",
                    "Nhẫn SJC 9,99",	
                    "PNJ Nhẫn 24K",
                    "PNJ NT 24K",
                    "Mi Hồng 985",
                    "Mi Hồng 980",
                    "Mi Hồng 750",
                    "PNJ NT 18K",
                    "Mi Hồng 680",
                    "Mi Hồng 610",
                    "PNJ NT 14K",
                    "PNJ NT 10K",
                    "Mi Hồng 950"
                                ]
   
        """Các thông số và giao diện"""
        self.app_width = 900
        self.app_height = 600
        
        """Căn giữa chương trình"""
        JustifyApp.center(self.root, self.app_width, self.app_height)
        
        """Background màu xanh của app"""
        self.canvas = tk.Canvas(
            self.root ,
            bg = "#3a6ff7",
            height = 600,
            width = 900,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge")
        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            50, 0, 50+800, 0+600,
            fill = "#ffffff",
            outline = "")
        
        self.canvas.create_rectangle(
            393, 65, 393+115, 65+2,
            fill = "#000000",
            outline = "")

        self.canvas.create_text(
            450.0, 44.5,
            text = "TRA CỨU GIÁ VÀNG",
            fill = "#000000",
            font = ("None", int(24.0)))

        self.canvas.create_text(
            136.0+15, 138.5,
            text = "Nhập loại vàng:",
            fill = "#000000",
            font = ("None", int(18.0)))

        self.canvas.create_text(
            117.5+10, 212.5,
            text = "Chọn ngày:",
            fill = "#000000",
            font = ("None", int(18.0)))
        
        """Ô nhập dữ liệu"""
        self.entry0_bg = self.canvas.create_image(
            330.0+25, 138.5,
            image = AppImage.get("TEXT_BOX_GOLD_IMG"))

        self.name = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0,
            font=("",13))
        
        self.name.bind("<Return>",self.find_button_clicked)
        
        self.name.place(
            x = 240.5+15, y = 116+10,
            width = 179.0,
            height = 30)
        
        self.name.bind("<KeyRelease>",self.update)
        self.name.bind("<FocusIn>", lambda event :Tk.select_entry(self.name,self.root))
        self.name.bind("<FocusOut>", self.toggle)
                
        """Ô chọn ngày tra"""
        self.cal = DateEntry(
                        takefocus = 0,
                        width=12,
                        background='darkblue',
                        foreground='white',
                        borderwidth=0,
                        showweeknumbers= False,
                        date_pattern= "dd/mm/yyyy",
                        maxdate= datetime.now(),
                        )
        
        self.cal.place(
                x = 117.5+80, y = 200,
                width = 100,
                height = 30)
        
        """Nút X để xoá ô nhập"""
        self.delete_button = tk.Button(
            image = AppImage.get("DELETE_BUTTON"),
            borderwidth = 0,
            highlightthickness = 0,
            command = self.delete_button_clicked,
            relief = "flat")

        self.delete_button.place(
            x = 429, y = 117,
            width = 24,
            height = 45)

        """Nút để tìm kiếm"""
        self.search_button = tk.Button(
            image = AppImage.get("SEARCH_BUTTON_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = self.find_button_clicked,
            relief = "flat")

        self.search_button.place(
            x = 453, y = 117,
            width = 35,
            height = 45)
        
        """Bảng kết quả"""
        columns = ("Đơn vị: đồng/lượng","Giá mua","Giá bán")
        self.my_tree = ttk.Treeview(self.root,columns=columns,style='MyStyle.Treeview',show='headings')
       
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        """Chỉnh sửa màu cho bảng"""
        self.style.configure("MyStyle.Treeview.Heading",
                             borderwidth=0,
                             foreground= 'black',
                             background='white',
                             fieldbackground = "white",
                             font = ("",18))
        self.style.configure("MyStyle.Treeview",
                        background='#E9E9E9',
                        foreground= 'black',
                        rowheight = 25, 
                        fieldbackground='white',
                        bordercolor = 'white',
                        borderwidth=0,
                        )
        
        """Thay đổi màu khi người dùng chọn"""
        self.style.map('MyStyle.Treeview',background = [('selected','#0E74EC')])
        
        """Định dạng cột"""
        self.my_tree.column("#0",width = 0, stretch =tk.NO)
        self.my_tree.column("Đơn vị: đồng/lượng",anchor = tk.W,width = 140)
        self.my_tree.column("Giá mua",anchor = tk.W,width = 80)
        self.my_tree.column("Giá bán",anchor = tk.W,width = 80)
        
        """Tạo heading của bảng"""
        self.my_tree.heading("#0",text = "",anchor = tk.W)
        self.my_tree.heading("Đơn vị: đồng/lượng",text = "Đơn vị: đồng/lượng",anchor = tk.W)
        self.my_tree.heading("Giá mua",text = "Giá mua",anchor = tk.W)
        self.my_tree.heading("Giá bán",text = "Giá bán",anchor = tk.W)
        
        """Chỉnh màu cho bảng"""
        self.my_tree.tag_configure("evenrow", background  = "lightblue")
        self.my_tree.tag_configure("oddrow", background  = "#fff")
        
        for col in columns:
            self.my_tree.heading(col, text=col, command= lambda _col=col : self.treeview_sort_column(_col, False))
            
        self.my_tree.place(
            x =65 ,y = 250,
            width = 770,
            height = 330
        )
              
        self.my_tree.bind("<Double-1>",self.chart_button_clicked)
        
        """Nút thu nhỏ màn hình"""
        self.minimize_button = tk.Button(
            image =AppImage.get("MINIMIZE_IMG") ,
            borderwidth = 0,
            highlightthickness = 0,
            command =   app.minimizeGUI,
            relief = "flat")

        self.minimize_button.place(
            x = 802 , y = 0,
            width = 24,
            height = 24)
        
        """Nút thoát"""
        self.exit_button = tk.Button(
        image = AppImage.get("EXIT_BUTTON_IMG"),
        borderwidth = 0,
        highlightthickness = 0,
        command = self.exit_button_clicked,
        relief = "flat")

        self.exit_button.place(
            x = 826, y = 0,
            width = 24,
            height = 24)
        
        """Ô gợi ý bên dưới ô người dùng nhập"""
        self.list_box = tk.Listbox(self.root,
                                   bg = "white",
                                   borderwidth=0, 
                                   highlightthickness=0,
                                   font=("Helvetica",10),
                                   activestyle= None,
                                   selectmode=tk.SINGLE
                                   )
        
        self.name.bind("<Tab>", self.fill_out)
        self.list_box.bind("<<ListboxSelect>>", self.fill_out)
    
    """Sort bảng"""
    def treeview_sort_column(self, col, reverse):
        """Nguồn tham khảo: https://stackoverflow.com/questions/1966929/tk-treeview-column-sort"""
        l = [(self.my_tree.set(k, col), k) for k in self.my_tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.my_tree.move(k, '', index)
            if self.my_tree.index(k) % 2 == 0:
                self.my_tree.item(k, tags="evenrow")
            else:
                self.my_tree.item(k, tags="oddrow")
        
        self.my_tree.heading(col, command=lambda _col=col :self.treeview_sort_column(_col, not reverse))   
    """Hàm khi người dùng nhấn Tab thì sẽ tự động điền cái gần đúng nhất cho người dùng"""
    def fill_out(self,event = None):
        self.name.delete(0,'end')
        selected = self.list_box.get(0)
        self.name.insert(0,selected)
        
        self.root.after(200, lambda: self.name.focus_set())
    
    """Hàm này để ẩn cái ô gợi ý đi"""        
    def toggle(self,event = None):
        self.list_box.place_forget()
   
    def update(self,event = None):
        if str(event.char) == "":
            key = str(event.keysym)
            if key == "Return":
                self.list_box.delete(0,tk.END)
                self.root.after(0,self.list_box.place_forget())
                return
            elif key == "Backspace":
                pass
            else:
                return
        self.list_box.place(
            x = 240.5+15, y = 116+50,
        )
        
        """Hiện gợi ý"""             
        typed = self.name.get()
        if typed == "":
            data =  self.list_name
        else:
            data = []
            list_of_name = process.extract(typed,self.list_name)
            list_of_name = [item[0] for item in list_of_name] 
            data = list_of_name  
             
        self.list_box.delete(0,tk.END)
        for item in data:
            self.list_box.insert(tk.END,item)
            self.list_box.config(width = 0,height = 0)
        
        self.root.after(1000,self.toggle) 
    
    """Các hàm hỗ trợ"""       
    def clear_table(self):
        if self.my_tree.get_children():
            for record in self.my_tree.get_children():
                 self.my_tree.delete(record)
    
    """Hàm không cho người dùng tìm rỗng"""      
    def check_input(self):
        if not self.name.get():
            messagebox.showwarning("Cảnh báo","  Chưa điền thông tin ")
            return False  

        return True
    
    """Các hàm để hiện thanh tiến trình"""
    def start_progress_bar(self):
        """List các luồng lấy dữ liệu từ server"""
        self.handle_thread = [
            threading.Thread(target = self.get_list_gold_threads),
            threading.Thread(target = self.get_value_of_chart)
            ]
        
        """Màu cho thanh tiến trình"""
        TROUGH_COLOR = 'white'
        BAR_COLOR = '#3A6FF7'
        
        """Khởi tạo 1 thanh tiến trình"""
        self.progress_bar = ttk.Progressbar(self.root,style="bar.Horizontal.TProgressbar",orient=tk.HORIZONTAL,length=300,mode = "indeterminate")
        self.progress_bar["maximum"] = 100
        
        """Chỉnh màu cho thanh tiến trình"""
        self.style.configure("bar.Horizontal.TProgressbar", 
                    troughcolor=TROUGH_COLOR, 
                    bordercolor=TROUGH_COLOR, 
                    background=BAR_COLOR, 
                    lightcolor=BAR_COLOR, 
                    darkcolor=BAR_COLOR,
                    borderwidth = 0)

        """Không cho client tra cứu cho đến khi nhận xong hết giá vàng"""
        self.search_button.configure(command=0)       
        self.name.unbind("<Return>")
        self.my_tree.unbind("<Double-1>")

        """Thanh tiến trình màu xanh"""
        self.progress_bar.place(x = 50,y = 250+330,
                    width = 760+40,height = 20)
        
        """Bắt đầu quá trình chạy thanh công cụ và kiểm tra luồng lấy dữ liệu từ server"""
     
        self.process_thread = self.handle_thread[self.flag]
        self.process_thread.setDaemon(True)
        self.progress_bar.start()
        self.root.after(20, lambda :self.process_thread.start())
        
        """Kiểm tra luồng"""
        self.root.after(20, self.check_thread)
    
    """Hàm bổ trợ cho hàm start_progress_bar"""    
    def check_thread(self):
        """Nếu luồng để nhận dữ liệu từ server vẫn đang hoạt động thì cập nhật giao diện"""
        if self.process_thread.is_alive():
            self.root.after(20, self.check_thread)
        else:
            """Nếu nhận hoàn tất thì dừng thanh tiến trình và xoá nó đi"""
            self.progress_bar.stop()
            self.progress_bar.destroy()
            
            """Bật lại nút tìm kiếm khi hoàn tất tiến trinh"""
            self.search_button.configure(command=self.find_button_clicked)          
            self.name.bind("<Return>",self.find_button_clicked)
            self.my_tree.bind("<Double-1>",self.chart_button_clicked)
            
            """Hiện kết quả lên giao diện"""
            if self.flag == 0:
                self.display_table()
            else:
                self.open_chart_window()
                   
    """Hàm để lấy dữ liệu từ server """
    def get_list_gold_threads(self):
        self.status,self.list_gold = self.client.start_query_from_server(self.name.get(),self.cal.get_date())
    
    """Hàm hiện kết quả lên bảng"""    
    def display_table(self):
        if self.status == DONE:
            """Mối lần người dùng tìm sẽ xoá bảng đi"""
            self.clear_table()
            count = 0
            for item in self.list_gold:
                if count % 2 == 0:
                    """Nhập vào bảng xen kẽ chẵn lẻ để làm bảng có sọc màu"""
                    self.my_tree.insert('',index='end',iid = count,text='',values= (item[0],item[1],item[2]),tags= ("evenrow",))
                else:
                    self.my_tree.insert('',index='end',iid = count,text='',values= (item[0],item[1],item[2]),tags = ("oddrow",)) 
                count += 1
            messagebox.showinfo("Trạng thái","   Tìm thành công")
        elif self.status == NOT_FOUND:
            messagebox.showerror("Trạng thái","   Không thành công")  
        elif self.status == ERROR:
            return
  
    """Hàm để lấy dữ liệu đồ thị từ server"""      
    def get_value_of_chart(self):
        """Lấy dòng người dùng đang chọn"""
        selected = self.my_tree.focus()
        value = self.my_tree.item(selected,'values')
    
        self.chart_name = value[0]
        
        """Tạo yêu cầu gửi tới server và trả về trạng thái,giá trị cột ngày, và 2 giá trị giá mua và giá bán theo từng ngày"""
        self.status,self.results = self.client.get_chart_value_from_server(self.chart_name)
        
    """Mở đồ thị giá vàng"""
    def open_chart_window(self,event=None):
        if self.status == ERROR or self.status == NOT_FOUND:
            return        
        
        self.valid_date = [datetime.strptime(item[0],"%d/%m/%Y") for item in self.results]
        self.buy = [int(item[1].replace(",","")) for item in self.results]
        self.sell = [int(item[2].replace(",","")) for item in self.results]
        
        fig, ax = plt.subplots()
        lines = []
        l, = ax.plot(self.valid_date, self.buy, label="Mua")
        lines.append(l)
        l, = ax.plot(self.valid_date, self.sell, label="Bán") 
        lines.append(l)
        
        fmt = '{x:,.0f}k'
        tick = mtick.StrMethodFormatter(fmt)
        ax.yaxis.set_major_formatter(tick)
        
        annot = ax.annotate("", xy=(0, 0), xytext=(-20, 20), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)

        def update_annot(line, idx):
            posx, posy = [line.get_xdata()[idx], line.get_ydata()[idx]]
            annot.xy = (mdates.date2num(posx), posy)
            text = f'Ngày: {posx.strftime("%#d/%m/%Y")}\n{line.get_label()}: {posy:,.0f}k'
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(0.4)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                for line in lines:
                    cont, ind = line.contains(event)
                    if cont:
                        update_annot(line, ind['ind'][0])
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                    else:
                        if vis:
                            annot.set_visible(False)
                            fig.canvas.draw_idle()

        fig.canvas.mpl_connect("motion_notify_event", hover)
        fig.canvas.manager.set_window_title('Đồ thị thay đổi giá vàng')
        
        plt.subplots_adjust(right=0.8)
        plt.title(f"{self.chart_name}",pad= 20)
        plt.gcf().autofmt_xdate()
        plt.grid(color = 'green', linestyle = '--', linewidth = 0.5)
        plt.legend(handles=lines,bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.show()
    
    """Hàm để xoá ô nhập dữ liệu"""         
    def delete_button_clicked(self,event = None):
        self.name.delete(0,'end')
        self.list_box.place_forget()
    
    """Hàm để thực hiện mở đồ thị"""
    def chart_button_clicked(self,event = None):
        region = self.my_tree.identify("region", event.x, event.y)
        if region == "heading":
            return
        self.flag = 1
        self.start_progress_bar()
    
    """Hàm để bắt đầu tìm kiếm"""
    def find_button_clicked(self,event = None):
        if self.check_input() == False:
            return
        self.flag = 0
        self.start_progress_bar()
    
    """Nút tắt trên góc phải màn hình"""  
    def exit_button_clicked(self):
        ask = messagebox.askyesno("Trạng thái","    Thoát ngay?   ",parent = self.root)
        if ask == 0:
            return
        else:          
            threading.Thread(target = self.client.client_disconnect).start()
          
"""Form để đăng ký"""  
class SignUpForm:
    def __init__(self,app):
        """Xoá màn hình"""
        Tk.clear_frame(app.root)
        
        """Khởi tạo"""
        self.app = app
        self.root = app.root
        self.client = app.client
        
        """Kích thước chương trình"""
        self.app_width = 600
        self.app_height = 300
        
        """Căn giữa màn hình"""
        JustifyApp.center(self.root,self.app_width,self.app_height)
        
        self.canvas = tk.Canvas(
            self.root,
            bg = "#3a7ff6",
            height = 300,
            width = 600,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge")
        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            100, 0, 100+400, 0+300,
            fill = "#ffffff",
            outline = "")

        self.canvas.create_text(
            299.5, 25.5,
            text = "ĐĂNG KÝ TÀI KHOẢN",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.entry0_bg = self.canvas.create_image(
            299.5, 89.0,
            image = AppImage.get("TEXT_BOX"))
        
        """Ô nhập tài khoản"""
        self.username = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0)

        self.username.delete(0,'end')
        self.username.bind("<Return>",self.sign_up_button_clicked)
        self.username.bind("<FocusIn>", lambda event : Tk.select_entry(self.username,self.root))
        
        self.username.place(
            x = 191.0+2, y = 64+22,
            width = 217.0,
            height = 25)

        self.entry1_bg = self.canvas.create_image(
            299.5, 150.0,
            image =  AppImage.get("TEXT_BOX"))
        
        """Ô nhập mật khẩu"""
        self.password = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0,
            show = "*")
        
        self.password.place(
            x = 191.0+2, y = 125+22,
            width = 217.0,
            height = 25)

        self.entry2_bg = self.canvas.create_image(
            299.5, 211.0,
            image =  AppImage.get("TEXT_BOX"))

        """Ô nhập lại mật khẩu"""
        self.re_enter_password = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0,
            show="*")
        
        self.re_enter_password.place(
            x = 191.0+2, y = 186+22,
            width = 217.0,
            height = 25)
        
        self.password.delete(0,'end')
        self.re_enter_password.delete(0,'end')
        
        """Bind nút với các chức năng"""
        self.password.bind("<Return>",self.sign_up_button_clicked)
        self.re_enter_password.bind("<Return>",self.sign_up_button_clicked)
        
        self.password.bind("<FocusIn>", lambda event :Tk.select_entry(self.password,self.root))
        self.re_enter_password.bind("<FocusIn>", lambda event :Tk.select_entry(self.re_enter_password,self.root))
        
        self.canvas.create_text(
            219.5+4, 78.5,
            text = "Tài khoản",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_text(
            219.5+5, 138.0,
            text = "Mật khẩu",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_text(
            242.0+15, 199.0,
            text = "Xác nhận mật khẩu",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_rectangle(
            264, 37, 264+72, 37+2,
            fill = "#000000",
            outline = "")

        self.sign_up = tk.Button(
            image = AppImage.get("SIGN_UP_IMG") ,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.sign_up_button_clicked,
            relief = "flat")

        self.sign_up.place(
            x = 248, y = 248,
            width = 103,
            height = 38)

        """Con mắt hiện ẩn mật khẩu"""
        self.show = tk.Button(
            image =  AppImage.get("SHOW_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            relief = "flat")

        self.show.bind("<Button-1>",(lambda event: self.show_and_hide_password(button = self.show,entry = (self.password,self.re_enter_password))))
        
        self.show.place(
            x = 371, y = 186,
            width = 47,
            height = 50)
        
        """Nút quay lại màn hình đăng nhập"""
        self.go_back = tk.Button(
            image = AppImage.get("GOBACK_IMG") ,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.previous_page,
            relief = "flat")
        
        self.go_back.place(
            x = 100 , y = 0,
            width = 24,
            height = 24
        )
        
        """Nút thu nhỏ chương trình xuống thanh công cụ"""
        self.minimize_button = tk.Button(
            image =  AppImage.get("MINIMIZE_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = app.minimizeGUI,
            relief = "flat")

        self.minimize_button.place(
            x = 452 , y = 0,
            width = 24,
            height = 24
            )
        
        """Nút thoát chương trình"""
        self.exit_button = tk.Button(
            image = AppImage.get("EXIT_BUTTON_IMG") ,
            borderwidth = 0,
            highlightthickness = 0,
            command = self.exit_button_clicked,
            relief = "flat"
            )

        self.exit_button.place(
            x = 476, y = 0,
            width = 24,
            height = 24
            )
    
    """Hàm ẩn hiện mật khẩu"""
    def show_and_hide_password(self,even = None,*args,**kwargs):
        for entry in kwargs["entry"]:
            if entry['show'] == "*":
                kwargs["button"].config(image =  AppImage.get("HIDE_IMG"))
                entry.config(show = "")
            else:
                kwargs["button"].config(image =  AppImage.get("SHOW_IMG"))
                entry.config(show = "*")

    """Hàm kiểm tra dữ liệu người dùng có hợp lệ hay không"""
    def checkInput(self,username,password, re_enter_password):
        if password == "" or username == "" or re_enter_password =="":
            messagebox.showwarning("Cảnh báo","Hãy điền đầy đủ các ô")
            return False
        msg = "Valid"
        if len(password) < 8:
            msg = "Mật khẩu phải từ 8 kí tự trở lên"
        elif re.search('[0-9]',password) is None:
            msg = "Mật khẩu phải chứa ít nhất 1 chữ số"
        elif re.search('[A-Z]',password) is None:
            msg = "Mật khẩu phải chứa ít nhất 1 kí tự viết hoa"
        
        if re_enter_password:
            if password != re_enter_password:
                messagebox.showwarning("Cảnh báo","Mật khẩu không khớp")
                return False
        if msg == "Valid":
            return True       
        else:
            messagebox.showwarning("Cảnh báo",msg)
            return False    
    
    """Hàm quay lại màn hình đăng nhập"""
    def previous_page(self):
        LoginForm(self.app)
    
    """Hàm dùng để đăng ký"""
    def sign_up_button_clicked(self,event = None):
        username = self.username.get()
        password = self.password.get()
        re_enter_password = self.re_enter_password.get()
        """Lấy thông tin từ các ô rồi kiểm tra, hợp lệ mới gửi qua server"""
        if self.checkInput(username,password,re_enter_password):
            status = self.client.register(username,password)
            if status == ALREADY_EXIT:
                messagebox.showwarning("Cảnh báo","Tài khoản đã tồn tại")
            elif status == SIGN_UP_SUCCESS:
                messagebox.showinfo("Trạng thái","Đăng kí thành công")
                self.login_form = LoginForm(self.app)
            elif status == ERROR:
                return
    
    """Nút thoát chương trình"""
    def exit_button_clicked(self):
        ask = messagebox.askyesno("Trạng thái","   Thoát ngay?   ",parent = self.root)
        if ask == 0:
            return
        else:           
            threading.Thread(target = self.client.client_disconnect).start()

"""Form để đăng nhập"""       
class LoginForm:
    def __init__(self,app):
        """Xoá màn hình"""
        Tk.clear_frame(app.root)
        
        """Khởi tạo"""
        self.app = app
        self.root = app.root
        self.client = app.client
        
        """Kích thước chương trình"""
        self.app_width = 600
        self.app_height = 300
        
        """Căn giữa chương trình"""
        JustifyApp.center(self.root,self.app_width,self.app_height)
        
        self.canvas = tk.Canvas(
            self.root,
            bg = "#3a7ff6",
            height = 300,
            width = 600,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge")
        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            100, 0, 100+400, 0+300,
            fill = "#ffffff",
            outline = "")

        self.canvas.create_text(
            298.5, 37.5,
            text = "ĐĂNG NHẬP VÀO SERVER",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.entry0_bg = self.canvas.create_image(
            298.5, 108.0,
            image = AppImage.get("TEXT_BOX")
            )

        """Ô nhập tên tài khoản"""    
        self.username = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0)

        self.username.place(
            x = 190.0+2, y = 83+20,
            width = 217.0,
            height = 25)
        
        self.username.delete(0,'end')
        self.username.bind("<Return>",self.login_button_clicked)
        self.username.bind("<FocusIn>", lambda event :Tk.select_entry(self.username,self.root))

        self.entry1_bg = self.canvas.create_image(
            298.5, 186.0,
            image = AppImage.get("TEXT_BOX"))

        """Ô nhập mật khẩu"""
        self.password = tk.Entry(
            bd = 0,
            bg = "#e9e9e9",
            highlightthickness = 0,
            show = "*")

        self.password.delete(0,'end')
        self.password.bind("<Return>",self.login_button_clicked)
        self.password.bind("<FocusIn>", lambda event :Tk.select_entry(self.password,self.root))
        
        self.password.place(
            x = 190.0+2, y = 161+21,
            width = 217.0,
            height = 25)

        self.canvas.create_text(
            218.5+5, 93.5+2,
            text = "Tài khoản",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_text(
            218.5+5, 174.0,
            text = "Mật khẩu",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_rectangle(
            264, 50, 264+72, 50+2,
            fill = "#000000",
            outline = "")

        """Nút đăng nhập"""
        self.login_button = tk.Button(
            image =   AppImage.get("SIGN_IN_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = self.login_button_clicked,
            relief = "flat")

        self.login_button.place(
            x = 246, y = 239,
            width = 103,
            height = 38)

        """Nút ẩn hiện mật khẩu"""
        self.show = tk.Button(
            image =   AppImage.get("SHOW_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            relief = "flat")

        self.show.bind("<Button-1>",(lambda event: self.show_and_hide_password(button = self.show,entry = (self.password,))))
        self.show.place(
            x = 370, y = 161,
            width = 47,
            height = 50)

        """Nút tạo tài khoản"""
        self.sign_up = tk.Button(
            image =   AppImage.get("CREATE_ACC_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = self.create_account_button_clicked,
            relief = "flat")

        self.sign_up.place(
            x = 339, y = 215,
            width = 78,
            height = 13)

        """Nút thu nhỏ chương trình"""
        self.minimize_button = tk.Button(
            image =   AppImage.get("MINIMIZE_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = app.minimizeGUI,
            relief = "flat")

        self.minimize_button.place(
            x = 452 , y = 0,
            width = 24,
            height = 24)
        
        """Nút thoát chương trình"""
        self.exit_button = tk.Button(
            image =   AppImage.get("EXIT_BUTTON_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = self.exit_button_clicked,
            relief = "flat")

        self.exit_button.place(
            x = 476, y = 0,
            width = 24,
            height = 24)
       
    """Hàm ẩn hiện mật khẩu"""
    def show_and_hide_password(self,even = None,*args,**kwargs):
        for entry in kwargs["entry"]: 
            if entry['show'] == "*":
                kwargs["button"].config(image = AppImage.get("HIDE_IMG"))
                entry.config(show = "")
            else:
                kwargs["button"].config(image = AppImage.get("SHOW_IMG"))
                entry.config(show = "*")
    
    """Kiểm tra input người dùng trước khi gửi"""            
    def checkInput(self,username,password):
        if password == "" or username == "":
            messagebox.showwarning("Cảnh báo","Hãy điền đầy đủ các ô")
            return False
        
        msg = "Valid"
        if len(password) < 8:
            msg = "Mật khẩu phải từ 8 kí tự trở lên"
        elif re.search('[0-9]',password) is None:
            msg = "Mật khẩu phải chứa ít nhất 1 chữ số"
        elif re.search('[A-Z]',password) is None:
            msg = "Mật khẩu phải chứa ít nhất 1 kí tự viết hoa"
        
        if msg == "Valid":
            return True       
        else:
            messagebox.showwarning("Cảnh báo",msg)
            return False     
    
    """Hàm hiện màn hình đăng ký"""
    def create_account_button_clicked(self,Even = None):
        SignUpForm(self.app)
    
    """Hàm để đăng nhập"""
    def login_button_clicked(self ,even = None):
        if self.checkInput(self.username.get(), self.password.get()):
            status = self.client.login(self.username.get(),self.password.get())
            if status == LOGIN_MSG_SUCCESS:
                messagebox.showinfo("Trạng thái","Đăng nhập thành công")
                QueryGoldForm(self.app)
            elif status == ALREADY_LOGGED:
                messagebox.showwarning("Trạng thái","Tài khoản đã đăng nhập\nHãy dùng tài khoản khác")
            elif status == WRONG_PASSWORD:
                messagebox.showerror("Trạng thái" , "Tài khoản hoặc mật khẩu không đúng") 
            elif status == NOT_SIGN_UP:
                messagebox.showwarning("Trạng thái" , "Tài khoản không tồn tại" )
            elif status == ERROR:
                return        
    
    """Thoát chương trình"""
    def exit_button_clicked(self):
        ask = messagebox.askyesno("Trạng thái","   Thoát ngay?   ",parent = self.root)
        if ask == 0:
            return
        else:         
            threading.Thread(target = self.client.client_disconnect).start()          
        
"""Form ban đầu để nhập địa chỉ IP SERVER""" 
class InputHostIp(tk.Frame):
    def __init__(self,app):
        """Khởi tạo"""
        self.app = app
        self.root = app.root
        self.client = app.client
        self.app_width = 600
        self.app_height = 300
        
        """ICON của chương trình"""
        self.root.tk.call('wm', 'iconphoto', self.root._w, AppImage.get("CLIENT_ICON"))
        
        """Căn giữa"""
        JustifyApp.center(self.root ,self.app_width,self.app_height)
    
        self.canvas = tk.Canvas(
            self.root ,
            bg = "#3a7ff6",
            height = 300,
            width = 600,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge")
        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            300, 0, 300+300, 0+300,
            fill = "#ffffff",
            outline = "")

        self.entry0_bg = self.canvas.create_image(
            449.5, 137.5,
            image = AppImage.get("HOST_INPUT"))

        """Ô nhập địa chỉ IP"""
        self.host_input_field = tk.Entry(
            bd = 0,
            bg = "#dedede",
            highlightthickness = 0)

        self.host_input_field.insert(tk.END,"HOST IP")
        self.host_input_field.bind("<Button-1>",(lambda event: self.host_input_field.delete(0,'end')))
        self.host_input_field.bind("<Return>", self.connect_button_clicked)
        self.host_input_field.bind("<FocusIn>", lambda event :Tk.select_entry(self.host_input_field,self.root))
        
        self.host_input_field.place(
            x = 380.0-3, y = 115+21,
            width = 139.0,
            height = 25)

        self.canvas.create_text(
            384.5, 126.5,
            text = "IP",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_text(
            450.5, 50.0,
            text = "NHẬP HOST IP",
            fill = "#000000",
            font = ("Roboto-Bold", int(12.0)))

        self.canvas.create_rectangle(
            428, 61, 428+44, 61+1,
            fill = "#000000",
            outline = "")

        self.b0 = tk.Button(
            image = AppImage.get("CONNECT_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = self.connect_button_clicked,
            relief = "flat")

        self.b0.place(
            x = 410, y = 219,
            width = 80,
            height = 40)
        
        self.canvas.create_text(
            140, 50.0,
            text = "CHƯƠNG TRÌNH TRA CỨU",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.canvas.create_text(
            33, 80,
            text = "GIÁ",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.canvas.create_text(
            85, 80,
            text = "VÀNG",
            fill = "#FAFF00",
            font = ("Roboto-Bold", int(15.0)))
        
        self.label1 = tk.Label(image=AppImage.get("GOLD_IMG"))
        self.label1.image = AppImage.get("GOLD_IMG")
        
        self.label1.place(
            x=150, y=90, 
            width= 100,
            height=100
            )
        
        self.canvas.create_text(
            80, 220,
            text = "Phát triển bởi:",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.canvas.create_text(
            142, 250,
            text = "20127067 - Trần Hồng Quân",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        self.canvas.create_text(
            154, 280,
            text = "20127665 - Dương Quang Vinh",
            fill = "#ffffff",
            font = ("Roboto-Bold", int(15.0)))
        
        """Nút thu nhỏ màn hình chương trình"""
        self.minimize_button = tk.Button(
            image =AppImage.get("MINIMIZE_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = self.app.minimizeGUI,
            relief = "flat")

        self.minimize_button.place(
            x = 552, y = 0,
            width = 24,
            height = 24)
        
        """Nút thoát chương trình"""
        self.exit_button = tk.Button(
            image = AppImage.get("EXIT_BUTTON_IMG"),
            borderwidth = 0,
            highlightthickness = 0,
            command = self.exit_button_clicked,
            relief = "flat")

        self.exit_button.place(
            x = 576, y = 0,
            width = 24,
            height = 24)
    
    """Hàm kiểm tra IPv4 của người dùng có hợp lệ không"""
    def check_IP_prefix(self):
        HOST_IP = self.host_input_field.get()
        if HOST_IP == "":
            messagebox.showwarning("Cảnh báo","Hãy điền vào ô")
            return False

        HOST_IP_PREFIX = HOST_IP.split('.') 
        if len(HOST_IP_PREFIX) < 4 or len(HOST_IP_PREFIX) > 4:
            messagebox.showerror("Lỗi","Không phải IPv4")
            return False
        else:
            for Val in HOST_IP_PREFIX:
                try:
                    Val = int(Val)
                    if Val > 255:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Lỗi","Không phải IPv4")
                    return False
                
    """Hàm kết nối đến Server"""
    def connect_button_clicked(self,event = None):
        if self.check_IP_prefix() == False:
            return
        HOST_IP = self.host_input_field.get()
        # print(HOST_IP)
                
        if self.client.start_connections(HOST_IP) == True:
            messagebox.showinfo("Trạng thái", f"Đã kết nối tới {HOST_IP}")
            self.login = LoginForm(self.app)
        else:
            messagebox.showerror("Trạng thái", "Không thể kết nối đến server")
    
    """Thoát chương trình"""
    def exit_button_clicked(self):
        self.root.destroy()
        sys.exit()
  