import collections
import json
import time

from selenium import webdriver
from bs4 import BeautifulSoup


def main():
    driver = webdriver.Chrome(executable_path="C:/Users/asaha/Downloads/chromedriver_win32/chromedriver.exe")

    limit = 200
    keys = set()

    with open('webmd.json', 'w') as file_handle:
        pagenumber = 0
        while len(keys) < limit:
            pagenumber += 1
            print(f'querying page {pagenumber}. {len(keys)}/{limit} results')
            driver.get(
                f"http://doctor.webmd.com/results?q=&pagenumber={pagenumber}&d=8&rd=8&sortby=distance&medicare=false&medicaid=false&newpatient=true&isvirtualvisit=false&minrating=0&pt=41.8951,-87.6218&zc=60611&city=Chicago&state=IL")
            page_source = driver.page_source

            print('parsing')
            soup = BeautifulSoup(page_source, 'html.parser')

            for results in soup.findAll('ul', attrs={'class': 'resultslist-content'}):
                for item in results.findAll('li'):
                    name = item.find('a', attrs={'class': 'prov-name'}).h2.text.strip()
                    specialty = item.find('p', attrs={'class': 'prov-specialty'}).text.strip()
                    address = item.address.text.strip()

                    key = name, specialty, address
                    if key in keys:
                        continue
                    keys.add(key)

                    phone_tag = item.find('span', attrs={'class': 'phoneicon'})
                    phone = None if phone_tag is None else phone_tag.parent.text.strip()
                    rating = float(item.find('div', attrs={'role': 'slider'}).attrs['aria-valuenow'])
                    num_ratings = int(item.find('span', attrs={'class': 'webmd-rate--number'}).text)

                    file_handle.write(json.dumps(collections.OrderedDict([
                        ('name', name),
                        ('specialty', specialty),
                        ('address', address),
                        ('phone', phone),
                        ('rating', rating),
                        ('num_ratings', num_ratings),
                    ])) + '\n')

            print('sleeping')
            time.sleep(5)


if __name__ == '__main__':
    main()
