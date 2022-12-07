from bs4 import BeautifulSoup
import requests
import json

fields = ['Name', 'Specialty', 'About', 'Location', 'PhoneNumber', 'Language', 'Medical Education', 'Residency',
          'BoardCerficiation', 'MedicalGroup', 'Hospital', 'Insurance', 'Ratings']

print("Scraping https://hospital.uillinois.edu")

html_response = requests.get('https://hospital.uillinois.edu/find-a-doctor/find-a-doctor-search-results?term=')
soup = BeautifulSoup(html_response.text, 'lxml')
specialists = soup.find_all('div', class_='specialist')
# print(specialists)

scraped_data = []
counter = 0
for specialist in specialists:
    specialist_data = {}
    name_and_suffix = specialist.find('p').find('a').contents
    name_and_suffix = name_and_suffix[0].split(',')
    specialist_data['Name'] = name_and_suffix[0].strip()
    specialist_data['Medical Education'] = list(map(lambda x: x.strip(), name_and_suffix[1:]))

    specialist_page_path = specialist.find('a').attrs['href']
    specialist_page = requests.get('https://hospital.uillinois.edu/' + specialist_page_path)
    specialist_soup = BeautifulSoup(specialist_page.text, 'lxml')

    e = specialist_soup.find('div', class_='buttons')

    c = e.find_next_sibling("p")
    if c:
        specialist_data['About'] = c.text.strip()
        e = c
    else:
        e = e.find_next_sibling('div')


    specialist_data['Specialty'] = []
    e = e.find_next_sibling("ul")
    for li in e.find_all('li'):
        specialist_data['Specialty'].append(li.text.strip())

    # specialist_data['Specialty'] = specialist.contents[3].contents[4].strip(),

    specialist_data['Location'] = []
    e = e.find_next_sibling('div')
    for string in e.strings:
        u = string.strip()
        if len(u) > 0:
            specialist_data['Location'].append(u)

    specialist_data['Location'] = ', '.join(specialist_data['Location'])

    counter += 1
    print(counter)
    scraped_data.append(specialist_data)

    # if counter > 5:
    #     break



# print(scraped_data)

with open('scraped_data.json', 'w') as fp:
    json.dump(scraped_data, fp, indent=2)

