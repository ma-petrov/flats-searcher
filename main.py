import re
import random
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Tag

PATH = '/Users/petrov/Repositories/cian-flat-searcher/'
CIAN_URL = 'https://www.cian.ru/cat.php'
TELEGRAM_URL = 'https://api.telegram.org/bot'
TOKEN = '2102130014:AAE3wac0wzuVVwj0DCY_jLlNjPqvaIECsNk'
CHAT_ID = '-631809644'

def add_log(text):
    date = datetime.datetime.now().strftime(r'%d.%m.%Y %H:%M')
    log = 'run at {} - {}'.format(date, text)
    if log[-1] != '\n': log += '\n'
    with open(PATH + 'main.log', 'a') as f:
        f.write(log)

def is_ids_new(flat_ids):
    '''
    Update data base of flat ids and returns new ids
    '''
    fname = PATH + 'flat_ids.csv'
    data = pd.read_csv(fname)
    data['flat_ids'] = data.flat_ids.apply(lambda x: str(x))
    new_ids = []
    for i in flat_ids:
        if data[data.flat_ids == i].shape[0] == 0:
            new_ids.append(i)
    data = pd.concat([data, pd.DataFrame({'flat_ids': new_ids})])
    data.to_csv(fname, index=False)
    return new_ids

def send_telegram(text):
    url = TELEGRAM_URL + TOKEN + '/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': text}
    response = requests.post(url, data=data)
    if response.status_code != 200:
        raise Exception("post_text error")

def reguest_with_proxy(url, params):
    '''
    Request with random proxy
    '''

    fname = PATH + 'proxies.csv'
    proxies = pd.read_csv(fname)
    n = random.randint(0, proxies.shape[0] - 1)
    protocol = proxies.loc[n, 'protocol']
    address = proxies.loc[n, 'address']
    try:
        response = requests.get(url=url, params=params, proxies={protocol: address})
        add_log('Successful request, used proxy address - {}'.format(address))
        return response
    except:
        text = 'Proxy SSLError, address - {}'.format(address)
        add_log(text)
        send_telegram(text)
        return None

def get_ads_list():
    '''
    get list of all offers urls
    '''
    
    maxprice = 70000
    params = {
        'currency': 2,
        'deal_type': 'rent',
        'engine_version': 2,
        'maxprice': maxprice,
        'foot_min': 12,
        'metro[0]': 12,
        'metro[1]': 15,
        'metro[2]': 68,
        'metro[3]': 159,
        'minarea': 50,
        'offer_type': 'flat',
        'room2': 1,
        'room3': 1,
        'sort': 'creation_date_desc',
        'type': 4 # Long rent period
    }

    response = reguest_with_proxy(CIAN_URL, params)

    if bool(re.search(r'www.cian.ru/captcha', response.url)):
        text = 'cian блокирует запрос капчей'
        add_log(text)
        h = int(now.strftime(r'%H'))
        print(response.url)
        if h > 7 and h < 23:
            send_telegram(text)

    else:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        flat_ids = []

        try:
            offers = soup.find(attrs={"data-name": "Offers"})
            for tag in offers.findAll('a'):
                if type(tag) == Tag and 'href' in tag.attrs:
                    href = tag['href']
                    if bool(re.search(r'www.cian.ru/rent/flat/[0-9]+', href)):
                        flat_ids.append(re.search(r'[0-9]+', href).group(0))
            add_log('number of parced offers - {}'.format(len(flat_ids)))

            new_ids = is_ids_new(flat_ids)

            if len(new_ids) > 0:
                add_log('найдены новые объявления')
                href = 'https://www.cian.ru/rent/flat/{}/'
                hrefs = ['{} - {}'.format(i + 1, href.format(x)) for i, x in enumerate(new_ids)]
                text = 'Новые объявления:\n' + '\n'.join(hrefs)
                send_telegram(text)
            else:
                add_log('новых объявлений нет')

        except AttributeError as e:
            if str(e) == "'NoneType' object has no attribute 'findAll'":
                text = 'ошибка при парсинге'
            else:
                text = 'непредвиденная ошибка'
            add_log(text)
            send_telegram(text)

if __name__ == '__main__':
    get_ads_list()