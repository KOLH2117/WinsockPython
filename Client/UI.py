import tkinter as tk
import tkinter as tk

from ctypes import windll
class Tk(tk.Tk):
    def overrideredirect(self, boolean=None):
        tk.Tk.overrideredirect(self, boolean)
        GWL_EXSTYLE=-20
        WS_EX_APPWINDOW=0x00040000
        WS_EX_TOOLWINDOW=0x00000080
        if boolean:
            print("Setting")
            hwnd = windll.user32.GetParent(self.winfo_id())
            style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_TOOLWINDOW
            style = style | WS_EX_APPWINDOW
            res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
        self.wm_withdraw()
        self.wm_deiconify()
        
def onKeyPress(event):
    print(event)
    # text.insert('end', 'You pressed %s\n' % (event, ))

root = tk.Tk()

root.geometry('600x300')
text = tk.Text(root, background='black', foreground='white', font=('Comic Sans MS', 12))
text.pack()
root.bind('<KeyPress>', onKeyPress)

lastClickX = 0
lastClickY = 0

def SaveLastClickPos(event):
    global lastClickX, lastClickY
    lastClickX = event.x
    lastClickY = event.y


def Dragging(event):
    x, y = event.x - lastClickX + root.winfo_x(), event.y - lastClickY + root.winfo_y()
    root.geometry("+%s+%s" % (x , y))



def motion1(event):
    x,y = root.winfo_pointerxy()
    # y = root.winfo_pointery()
    abs_coord_x =  root.winfo_rootx()
    abs_coord_y =  root.winfo_rooty()
    # print(abs_coord_x, abs_coord_y)
    x1, y1 = event.x, event.y
    # x = x - x1;
    # y = y - y1;
    print('{}, {}'.format(x, y))
    print('{}, {}'.format(x1, y1))

abs_coord_x =  root.winfo_rootx()
abs_coord_y =  root.winfo_rooty()
print(abs_coord_x, abs_coord_y)
def motion(event):
    x,y = root.winfo_pointerxy()
    # y = root.winfo_pointery()
    abs_coord_x =  root.winfo_rootx()
    abs_coord_y =  root.winfo_rooty()
    print(abs_coord_x, abs_coord_y)
    x1, y1 = event.x, event.y
    x2 = abs_coord_x - x1;
    y2 = abs_coord_x - y1;
    print('{}, {}'.format(x, y))
    print('{}, {}'.format(x1, y1))
    
    root.geometry(f"600x300+{int(x2)}+{int(y2)}")

# root.bind('<Motion>', motion1)
# root.bind('<B1-Motion>', motion)
root.bind('<Button-1>', SaveLastClickPos)
root.bind('<B1-Motion>', move_window)
Tk.overrideredirect(root,1)
root.mainloop()


# import tkinter as tk
# import tkinter.ttk as ttk
# from ctypes import windll

# GWL_EXSTYLE=-20
# WS_EX_APPWINDOW=0x00040000
# WS_EX_TOOLWINDOW=0x00000080

# def set_appwindow(root):
#     hwnd = windll.user32.GetParent(root.winfo_id())
#     style = windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
#     style = style & ~WS_EX_TOOLWINDOW
#     style = style | WS_EX_APPWINDOW
#     res = windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)
#     # re-assert the new window style
#     root.wm_withdraw()
#     root.after(10, lambda: root.wm_deiconify())

# def main():
#     root = tk.Tk()
#     root.wm_title("AppWindow Test")
#     button = ttk.Button(root, text='Exit', command=lambda: root.destroy())
#     button.place(x=10,y=10)
#     root.overrideredirect(True)
#     root.after(10, lambda: set_appwindow(root))
#     root.mainloop()

# if __name__ == '__main__':
#     main()