# @name         Product Scraper
# @version      6.0
# @description  collects data from categories on website.
# @author       Insula415

import bs4
import requests
import csv
import pandas as pd  
import os
import sys
import shopify

from termcolor import colored
from bs4 import BeautifulSoup
from time import sleep
from os.path import exists

from selenium import webdriver
from selenium.webdriver.common.by import By 

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from win10toast import ToastNotifier


class Scrape:
    def checkTitle(self, title):
        # ******************* checking for special characters  ******************* #
        special_characters = '[{!@#$%£^&*()-_=+\|]}[{;:/?.>,<}]"'

        if any(s in special_characters for s in title):
            return True
        else:
            return False   
            
    def __init__(self):
        shop_url = "https://.myshopify.com/"
        api_version = "2022-07"
        private_app_password = "private app password"
        session = shopify.Session(shop_url, api_version, private_app_password)
        shopify.ShopifyResource.activate_session(session)
        user = "user"
        pw = "pass"

        signedIn = True
        googleOpen = True

        # ******************* Setting global variables ******************* #
        global toaster
        toaster = ToastNotifier()
        global dontCarryOn 
        dontCarryOn = False

        with open("categories.txt","r") as f: # reading categories
            categories = f.readlines()
        with open("categories.txt","r") as f:
            catCount = sum(1 for line in f)
 
        print(" ")
        print(colored(f"Scraping {catCount} categories","green"))
        print(" ")

        # ******************* User arguments ******************* #
        args = sys.argv[1:]

        if "-help" in args:
            print("open google: -g, -google")
            print("sign in to program: -s, -signin")
            quit()
        else: None
        
        if "-signin" in args: # if user is wanting to sign in
            signedIn = False 
        else: None

        if "-google" in args: # if user is wanting to open google
            googleOpen = False 
        else: None 

        if googleOpen: None #if google is already open or not
        else:
            print("opening google")
            os.system("start cmd /k chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\chrome")
            sleep(1)
            print("closing cmd")
            os.system("taskkill /f /im cmd.exe")

        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        self.driver = webdriver.Chrome(options=options, service=Service(ChromeDriverManager().install()))
        self.driver.implicitly_wait(10)

        if signedIn: # if user is signed in 
            None
        else:
            print(colored("Logging in...","green"))
            self.driver.get("https://login")
            sleep(1)
            self.driver.find_element(By.NAME, "login[username]").send_keys(user) # sending username
            sleep(2)
            self.driver.find_element(By.NAME, "login[password]").send_keys(pw) # sending password
            sleep(2)
            self.driver.find_element(By.XPATH, "/html/body/div[2]/main/div[2]/div/div[3]/div/form/fieldset/div[4]/button/span") # clicking submit
            print(colored("Successfully logged in","green"))
        
        html = self.driver.page_source # getting current page source
        soup = BeautifulSoup(html, features="html.parser")

        
        # ******************* Scraping categories from categories.txt ******************* #
        for url in categories:
            try:
                self.driver.get(url) # going to category 
                html = self.driver.page_source # getting current page source
                soup = BeautifulSoup(html, features="html.parser")

                catTitle = soup.find('h1', {'class':'page-title'}) # getting page title and making it a folder
                main_dir = catTitle.text.strip()

            except Exception as e: # if url is invalid
                print(colored(f"Couldn't fetch {url}","red"))
                print(colored("ERROR:","red"))
                print(colored(f"{e}","red"))
                continue

            titleOkay = self.checkTitle(main_dir) # checking if title is okay to use, if not changing it
            if titleOkay:
                print(colored(f"{main_dir}", "red"))
                main_dir = ''.join(e for e in main_dir if e.isalnum())
                print(colored(f"Updated: {main_dir}","green"))
            else: None

  
            main_collection = shopify.CustomCollection()
            main_collection.title = main_dir
            main_collection.published = True
            main_collection.id
            main_collection.save()
            mainCollectionID = main_collection.id
            print("***")
            print(colored(f"Custom collection '{main_collection.title}' created with the id {main_collection.id}", "green"))
            print("***")
            href_list = []
            cards = soup.find_all("a", attrs={"class":"card__link"})    
            for card in cards:
                get_href = card["href"]
                href_list.append(get_href) # getting all the card links
            self.hrefs(href_list, main_dir, mainCollectionID)

    
    def hrefs(self, href_list, main_dir, mainCollectionID):
        # ******************* Going into first cards and collecting second card titles ******************* #
        for url in href_list:
            a = requests.get(url)
            s = bs4.BeautifulSoup(a.text, features="html.parser")
            title = s.find('h1', {'class':'page-title'})
            sub_dir = title.text.strip()

            titleOkay = self.checkTitle(sub_dir) # checking if title is okay
            if titleOkay:
                print(colored(f"{sub_dir}", "red"))
                sub_dir = ''.join(e for e in sub_dir if e.isalnum())
                print(colored(f"updated: {sub_dir}","green"))
            else: None
  
            sub_collection = shopify.CustomCollection()
            sub_collection.title = sub_dir
            sub_collection.published = True
            sub_collection.id
            sub_collection.save()
            subCollectionID = sub_collection.id
            print("***")
            print(colored(f"Custom collection '{sub_collection.title}' created with the id {sub_collection.id}", "green"))
            print("***")

            card_links = s.find_all("a", {"class":"card__link"}) # for every product in card link
            for link in card_links:
                href = link["href"]
                # print(colored(f"Link: {href}","blue"))
                self.scrape(href, main_dir, sub_dir, mainCollectionID, subCollectionID)
                
    def scrape(self, href, main_dir, sub_dir, mainCollectionID, subCollectionID):
        global dirUpdated
        global spreadsheetCount
        global productCount 
        dirUpdated = False
        spreadsheetCount = 0
        productCount = 0

        print(colored(f"Fetching {href}","blue"))
        self.driver.get(href)
        html = self.driver.page_source # getting current page source
        soup = BeautifulSoup(html, features="html.parser")
        t = soup.find('h1', {'class':'page-title'}) # getting title and saving it as a sub directory
        print(colored(f"title: {t.text}","blue"))
        subsub_dir = t.text.strip()
        titleOkay = self.checkTitle(subsub_dir)
        if titleOkay:
            print(colored(f"{subsub_dir}", "red"))
            subsub_dir = ''.join(e for e in subsub_dir if e.isalnum())
            print(colored(f"Updated: {subsub_dir}","green"))
        else: None

        subsub_collection = shopify.CustomCollection()
        subsub_collection.title = subsub_dir
        subsub_collection.published = True
        subsub_collection.id
        subsub_collection.save()
        print("***")
        print(colored(f"Custom collection '{subsub_collection.title}' created with the id {subsub_collection.id}", "green"))
        print("***")

    
        try:
            details = soup.find_all("a", attrs={"class":"grid-link"})
            # srcs = soup.find_all("img", attrs={"class":"grid-image"})
        except:
            print(colored("Something went wrong finding product information", "red"))
            print(colored("Are you on a category?", "blue"))
        
        try:
            prices = soup.find_all("span", attrs={"class":"special-price"})
        except:
            print(colored("Couldn't find prices of products", "red"))
            print(colored("Are you logged in?", "blue"))
        

        href_list = []
        title_list = []
        price_list = []

        # ******************* Searching through classes to find product data ******************* #
        for i in details:
            get_href = i["href"]
            href_list.append(get_href)
            title_list.append(i.text)

        for p in prices:
            p = p.text
            x = p.replace("Special Price", " ")
            y = x.replace("£"," ")
            price_list.append(y.strip())
        
        if not price_list:
            print(colored("Couldn't get prices","red"))
            print(colored("Make sure you're on a category","blue"))
            print(price_list)
            sleep(5)
        else:
            None

        tags = f"{main_dir}, {sub_dir}, {subsub_dir}" # adding tags of the main directories

        for title, url, price in zip(title_list, href_list, price_list):
            print("*")
            print(colored(f"{title}","green"))
            if "," in price: # if price contains a comma
                price = price.replace(',', '')
                price = float(price)
            else:
                price = float(price)

            handle = "-".join(title.split()).lower() # formatting the titles for the shopify handle

            a = requests.get(url)
            soup = BeautifulSoup(a.text, features="html.parser")
        
            d = soup.find('div', {'class':'product__accordion-content-inner'})
            desc = d.text # description
            print(colored("Collected description","green"))


            table = soup.find('table', {'class':'product__techspec'})
            print(colored("Collected table","green"))

            final = str(desc) + "<br>" + "<br>" + str(table)

            product = shopify.Product()
            product.title = title
            product.body_html = final
            product.vendor = "VENDOR"
            product.tags = tags
            product.id

            print("Old price:",price)
            percent = price/100*45 # 45% of price
            price = price + percent # adding percentage back to price
            price = format(price, '.2f')
            price = float(price)
            print("Updated price:",price)    
            variant = shopify.Variant({'price': price, 'requires_shipping': False, "inventory_management": "shopify", "inventory_quantity": "999", "inventory_tracker":"shopify"})
            product.variants = [variant]

            
            all_images = []
            count = 0
            varCount = 0
            product_images = soup.find_all('a', {'class':'gallery__thumb-link'}) 
            # finding all the images and adding them to a list
            for i in product_images:
                get_href = i["href"]
                all_images.append(get_href)
                count += 1

            print(colored(f"Adding {count} images", "green"))
            
            # creating variables from image list
            shopify_images=[]
            dict = {}
            for url in all_images:
                varCount += 1
                var = "image" + str(varCount+1)
                dict[var] = shopify.Image({'src':f'{url}'})
                shopify_images.append(dict[var])
            product.images = shopify_images # adding them to the product images
            product.save()

            # adding the product to created collections
            a = shopify.Collect({ 'product_id': product.id, 'collection_id': mainCollectionID })
            a.save()
            print(colored(f"'{title}' ({product.id}) was added to '{mainCollectionID}'", "green"))
            b = shopify.Collect({ 'product_id': product.id, 'collection_id': subCollectionID })
            b.save()
            print(colored(f"'{title}' ({product.id}) was added to '{subCollectionID}'", "green"))
            c = shopify.Collect({ 'product_id': product.id, 'collection_id': subsub_collection.id })
            c.save()
            print(colored(f"'{title}' ({product.id}) was added to '{subsub_collection.id}'", "green"))

            print("*")
            product.save()

            with open("products.txt", "a") as f:
                f.write(title + " "+ str(product.id) + "\n")
                
    
    # def check_qty(): # checking if products are out of stock and editing them.
    #     test = []
    #     for i in soup.find_all('div', {'class':'grid-item'}):
    #         test.append(i.text)
        
    #     for i in test:
    #         i = i.lower()
    #         if "out of stock" in i:
    #             print(i)
    # product = shopify.Product.find(292082188312)


    shopify.ShopifyResource.clear_session() # clearing the session



Scrape()
