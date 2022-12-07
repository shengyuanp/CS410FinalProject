# Purpose: scrape physician information from University of Chicago website: https://www.uchicagomedicine.org
# Input: Provide a list of starting urls for each specialty
# Output: 
# 1. a list of urls to individual physician biography pages
# 2. scraped and stacked data saved as json file with each record representing a unique physician

from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
import urllib
import time
import requests
import json
import re
import numpy

#create a webdriver object and set options for headless browsing
options = Options()
options.add_argument("user-agent=Mozilla/5.0")
options.headless = True
driver = webdriver.Chrome('./chromedriver_win32/chromedriver.exe',options=options)

#uses webdriver object to execute javascript code and get dynamically loaded webcontent
def get_js_soup(url,driver):
    driver.get(url)
    res_html = driver.execute_script('return document.body.innerHTML')
    soup = BeautifulSoup(res_html,'html.parser') #beautiful soup object to be used for parsing html content
    return soup

#extracts all Physician Profile page urls from the Specialty Directory Listing Page
def scrape_dir_page(dir_url,driver):
    print ('-'*20,'Scraping directory page','-'*20)
    links = []
    base_url = 'https://www.uchicagomedicine.org'
    #execute js on webpage to load physician listings on webpage and get ready to parse the loaded HTML 
    soup = get_js_soup(dir_url,driver)     
    options = soup.find_all("select",class_="selectpicker")
    for o in options:
        selections=o.find_all('option')
        for s in selections:
            if 'physician' in s['value']:
                links.append(base_url+s['value'])
    print ('-'*20,'Found {} physician profile urls'.format(len(links)),'-'*20)
    return links

physician_links=[]
# get physician links
dir_urls = ['https://www.uchicagomedicine.org/find-a-physician?specialtyId=7cc15a20-416e-4ee1-a285-d3c969af0034&specialty=Family%20Medicine'
            ,'https://www.uchicagomedicine.org/find-a-physician?specialtyId=7affe810-fff6-4c99-b368-0d481bd2b8b1&specialty=Geriatric%20Medicine'
            ,'https://www.uchicagomedicine.org/find-a-physician?specialtyId=96f4bc38-44fa-412e-9c8f-9ff5971cc1f3&specialty=Internal%20Medicine'
            ,'https://www.uchicagomedicine.org/find-a-physician?specialtyId=bb253492-3aac-4710-ad38-4cb5c70a6f41&specialty=Neurology'
            ,'https://www.uchicagomedicine.org/find-a-physician?specialtyId=0e103803-6d56-46ce-9b45-214d2ed3527d&specialty=Obstetrics%20and%20Gynecology%20(OB%2FGYN)'
            ,'https://www.uchicagomedicine.org/find-a-physician?specialtyId=0a4efeeb-2027-49aa-b183-56c2f006d738&specialty=Primary%20Care'
            ,'https://www.uchicagomedicine.org/find-a-physician?specialtyId=9ef7e68b-9e30-4072-9b05-46e39023bb65&specialty=Ophthalmology'
            ,'https://www.uchicagomedicine.org/find-a-physician?specialtyId=bef4de24-639e-45d0-8b08-28467717a190&specialty=Optometry'
            ,'https://www.uchicagomedicine.org/find-a-physician?specialtyId=01556aaf-2f57-4e79-8e16-960d22a41d65&specialty=Pediatrics']

for dir_url in dir_urls:
    physician_links=physician_links+scrape_dir_page(dir_urls[8],driver)

# deduplicate url list, sometimes, the same doctor can be listed under multiple different departments
links=list(dict.fromkeys(physician_links))

# save the scraped physician urls
with open('physicianlinks.txt', 'w') as f:
    for line in links:
        f.write(f"{line}\n")

# use url to individual physician bio page to scrape physician data
def scrape_single_physician(url,driver):
    phy_data = {}
    soup = get_js_soup(url,driver) 
    # get physician specialty, there can be more than one
    spec=soup.find("div",class_="panel-collapse collapse").find('ul')
    phy_data['Specialty']=[]
    if spec!=None:
        for li in spec.find_all('li'):
            phy_data['Specialty'].append(li.text)
    # get physician name and title (there can be multiple titles)
    desc=soup.find("div",class_="doctor-banner-details")
    nametitle=desc.find("h1").contents
    if nametitle==[]:
        phy_data['Title']=''
        phy_data['Name']=url.split('/')[-1].replace("-", " " )
    else:
        phy_data['Name']=nametitle[0].lower().split(',')[0]
        phy_data['Title']=''.join(nametitle[0].lower().split(',')[1:])
    accord=soup.find_all("div",class_="panel-collapse collapse")
    # get area of expertise if exists
    phy_data['AreaofExpertise']=[]
    if len(accord[0].find_all('ul'))>1:
        for a in accord[0].find_all('ul')[1]:
            if a.text!='\n':
                phy_data['AreaofExpertise'].append(a.text)
    # get personal summary (language, education, board certification)
    for p,li in zip(accord[2].find_all('p'),accord[2].find_all('li')):
        phy_data[p.text]=li.text
    # get accepted insurance if exist
    phy_data['insurance']=[]
    for li in accord[3].find_all('li'):
        phy_data['insurance'].append(li.text)
    # get ratings
    if len(accord)>5:
        phy_data['ratings']=accord[4].find('a').text
    return(phy_data)

alldata=[]
# loop through each physician link, scrape relevant information, and append all scraped records 
for url in links:
    alldata.append(scrape_single_physician(url,driver))

# save appended records to json format
with open('physician_data.json', 'w') as f:
    json.dump(alldata, f, indent=2)