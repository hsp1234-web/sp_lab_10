import requests
from bs4 import BeautifulSoup

url = "https://www.taifex.com.tw/cht/3/dlFutDailyMarketView"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

forms = soup.find_all('form')
for i, form in enumerate(forms):
    print(f"--- Form {i} ---")
    print(f"Action: {form.get('action')}")
    print(f"Method: {form.get('method')}")
    inputs = form.find_all('input')
    for inp in inputs:
        print(f"  Input: name={inp.get('name')}, value={inp.get('value')}, type={inp.get('type')}")
    selects = form.find_all('select')
    for sel in selects:
        print(f"  Select: name={sel.get('name')}, id={sel.get('id')}")
    buttons = form.find_all('button')
    for btn in buttons:
        print(f"  Button: id={btn.get('id')}, text={btn.text.strip()}")
