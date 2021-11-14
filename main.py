import re
import json
import random
import requests
import datetime
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Tag

# log types
INFO = 'INFO'
WARNING = 'WARNING'
ERROR = 'ERROR'
NOTYPE = 'NOTYPE'

# paths and urls
PATH = '/Users/petrov/Repositories/cian-flat-searcher/'
CIAN_URL = 'https://www.cian.ru/cat.php'
TELEGRAM_URL = 'https://api.telegram.org/bot'
TOKEN = '2102130014:AAE3wac0wzuVVwj0DCY_jLlNjPqvaIECsNk'
CHAT_ID = '-631809644'

def add_log(text, log_type=INFO):
    '''
    Print log to main.log file
    '''

    if log_type in [INFO, WARNING, ERROR]:
        log = '{} - {}'.format(log_type, text)
    else:
        log = text
    if log[-1] != '\n': log += '\n'
    with open(PATH + 'logs/output.log', 'a') as f:
        f.write(log)

def is_ids_new(flat_ids):
    '''
    Update data base of flat ids and returns new ids
    '''

    fname = PATH + 'data/flat_ids.csv'
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

    fname = PATH + 'data/proxies.csv'
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
        add_log(text, log_type=ERROR)
        send_telegram(text)
        return None

def load_params():
    '''
    get parameters of GET request from file
    '''

    with open(PATH + 'data/params.json', 'r') as f:
        return json.loads(f.read())

def generate_message(flat_ids):
    '''
    Generate message from flat_ids to links
    '''

    href = 'https://www.cian.ru/rent/flat/{}/'
    hrefs = ['{} - {}'.format(i + 1, href.format(x)) for i, x in enumerate(flat_ids)]
    return 'Новые объявления:\n' + '\n'.join(hrefs)

def main():
    '''
    get list of all offers urls
    '''

    # logging start time
    date = datetime.datetime.now()
    add_log('\nRun at {}'.format(date.strftime(r'%d.%m.%Y %H:%M:%S')), log_type=NOTYPE)

    params = load_params()
    response = reguest_with_proxy(CIAN_URL, params)
    add_log('request URL is {}'.format(response.url))

    if bool(re.search(r'www.cian.ru/captcha', response.url)):
        text = 'cian блокирует запрос капчей'
        add_log(text)
        h = int(date.strftime(r'%H'))
        if h > 7 and h < 23:
            send_telegram(text)

    else:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        flat_ids = []

        try:
            # parce
            offers = soup.find(attrs={'data-name': 'Offers'})
            for tag in offers.findAll('a'):
                if type(tag) == Tag and 'href' in tag.attrs:
                    href = tag['href']
                    if bool(re.search(r'www.cian.ru/rent/flat/[0-9]+', href)):
                        flat_ids.append(re.search(r'[0-9]+', href).group(0))
            add_log('number of parced offers - {}'.format(len(flat_ids)))

            # get new offres from all recieved
            new_ids = is_ids_new(flat_ids)

            # check if there is new offers and send message
            if len(new_ids) > 0:
                add_log('new offers were found')
                send_telegram(generate_message(new_ids))
            else:
                add_log('no new offers')

        except AttributeError as e:
            text = str(e)
            add_log(text)
            send_telegram(text)

if __name__ == '__main__':
    main()