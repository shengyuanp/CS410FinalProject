from bs4 import BeautifulSoup
import requests
import json
from string import ascii_uppercase as alph


print("Scraping https://www.mayoclinic.org/")
scraped_data = {}
condition_links = set()
total_condition_count = 0
for letter in alph:
    url = "https://www.mayoclinic.org/diseases-conditions/index?letter=" + letter
    html_response = requests.get(url)
    soup = BeautifulSoup(html_response.text, 'lxml')
    links = soup.find_all('a', href=True)
    for link in links:
        if "/symptoms-causes/" in link.attrs.get('href'):
            condition_links.add(link.attrs.get('href'))
            total_condition_count += 1

print(f"total conditions count {total_condition_count}")
processed_conditions_count = 0
for link in condition_links:
    url = "https://www.mayoclinic.org" + link
    html_response = requests.get(url, headers={'User-Agent': 'pinto-beans-493098'} )
    if html_response.status_code != 200:
        print(url + " gave response code " + str(html_response.status_code) )

    soup = BeautifulSoup(html_response.text, 'lxml')

    condition_name = soup.find_all('title')[0].text.split('-')[0].strip()

    symptom_section = None
    sections = soup.find_all('h2')
    for section in sections:
        if len(section.contents) == 1 and section.contents[0] == 'Symptoms':
            symptom_section = section

    if symptom_section is None:
        continue

    links2 = soup.find_all('a', href=True)
    dept_link = None
    for link2 in links2:
        if "/doctors-departments/" in link2.attrs.get('href'):
            dept_link = link2.attrs.get('href')
            break

    if dept_link is None:
        print("no dept link for " + condition_name)
        continue

    # iterate over all siblings, until hitting another h2/h3
    cur_section = symptom_section.find_next_sibling()
    symptom_description_texts = set()
    loop_counter = 0
    while cur_section is not None and cur_section.name != 'h2' and cur_section.name != 'h3' and loop_counter < 200:
        loop_counter += 1
        if len(cur_section.text) > 0 and "\n" in cur_section.text:
            symptoms_list = cur_section.text.split("\n")
            for symptom in symptoms_list:
                if len(symptom) > 0:
                    symptom_description_texts.add(symptom)
        cur_section = cur_section.find_next_sibling()


    dept_url = "https://www.mayoclinic.org" + dept_link
    dept_response = requests.get(dept_url, headers={'User-Agent': 'pinto-beans-493098'})
    if dept_response.status_code != 200:
        print(dept_url + " gave response code " + str(dept_response.status_code) )

    dept_soup = BeautifulSoup(dept_response.text, 'lxml')
    dept_sections = dept_soup.find_all('h3')

    departments_header = None
    for dept_section in dept_sections:
        if dept_section.text == 'Departments that treat this condition':
            departments_header = dept_section
            break
    if departments_header is None:
        continue


    cur_section = departments_header.find_next_sibling()
    department_texts = set()
    loop_counter = 0
    while cur_section is not None and cur_section.name != 'h2' and cur_section.name != 'h3' and loop_counter < 200:
        loop_counter += 1
        if len(cur_section.text) > 0 and "\n" in cur_section.text:
            depts_list = cur_section.text.split("\n")
            for dept in depts_list:
                if len(dept) > 0:
                    department_texts.add(dept)
        cur_section = cur_section.find_next_sibling()

    scraped_data[condition_name] = {
        'symptoms': list(symptom_description_texts),
        'specialties': list(department_texts),
    }
    print(f'finished processing {condition_name}')
    # and concatenate all text content with /n until hitting a
    processed_conditions_count += 1
    print(f"{processed_conditions_count*100/total_condition_count} % complete ({processed_conditions_count}/{total_condition_count})")


with open('mayo_data.json', 'w') as fp:
    json.dump(scraped_data, fp, indent=2)






