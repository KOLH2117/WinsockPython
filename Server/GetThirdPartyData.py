import requests
from bs4 import BeautifulSoup

class ThirdPartyServerData:
    def __init__(self):
        return
    
    """Hàm lấy giá vàng"""
    def get_gold_list(date):
        all_golds = {}
        
        """Sử dụng thư viện requests để lấy html response"""
        URL = f"https://tygia.com/api.php?column=0&cols=1&title=1&chart=0&gold=1&rate=0&expand=2&nganhang=VIETCOM&ngay={date}"
        try:
            html_text = requests.get(URL).text
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.ConnectionError
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout
        else:
            soup = BeautifulSoup(html_text,"lxml")
        
            try:
                """Lấy ngày đang tra cứu từ html"""
                present_day = soup.find("span",id = "datepk1")
                
                """Dựa vào class và id để tìm lấy dữ liệu từ html"""
                list_gold = soup.find_all("tr",class_ = "rmore rmore1")
                list_gold.append(soup.find("tr",id = "SJCH_Ch_Minh"))
                list_gold.append(soup.find("tr",id = "SJCH_N_i"))
                list_gold.append(soup.find("tr", id = "DOJIH_N_iAVPL"))
                list_gold.append(soup.find("tr", id = "DOJIH_Ch_MinhAVPL"))
                list_gold.extend(soup.find_all("tr",class_ = "rmore3"))
                list_gold.extend(soup.find_all("tr",class_ = "rmore4"))
                list_gold.extend(soup.find_all("tr",class_ = "rmore5"))
                """Danh sách trả về gồm loại vàng,giá mua,giá bán"""
                values = []
                for gold in list_gold:
                    if gold:
                        """Tìm đến thẻ chứa loại vàng"""
                        name = gold.find("td",class_ = "c1 text-left")
                        
                        """Tìm đến thẻ chứa giá mua"""
                        buy = name.find_next("td")
                        
                        """Nếu tồn tại thì trích xuất giá mua ra"""
                        if buy.find_all('div'):
                            buy_price = buy.div.div.span.text
                        else:
                            """Nếu không có thẻ mua thì cho nó bằng 0"""
                            buy_price = "0"
                        
                        """Tìm đến thẻ chứa giá mua"""
                        sell = buy.find_next("td")
                        
                        """Nếu tồn tại thì trích xuất giá mua ra"""
                        if sell.find_all('div'):
                            sell_price = sell.div.div.span.text
                        else:
                            """Nếu không có thẻ mua thì cho nó bằng 0"""
                            sell_price = "0"
                        
                        """Xoá khoảng trắn thừa trong loại vàng"""
                        name = " ".join(name.text.split())
                        
                        
                        """Trường hợp đặc biệt đối với Mi Hồng 950 third party bị lộn giá mua với giá bán"""
                        """Đã kiểm chứng với nhiều trang lấy giá vàng khác"""
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
                """Trả về dạng dict với key là ngày tra"""
                all_golds[present_day.text] = values 
                return all_golds
            except:
                return None


