from .BaseScraper import BaseScraper
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import random
import re


class TrainsplitScraper(BaseScraper):
    websiteName = "Trainsplit"
    websiteUrl = "https://www.trainsplit.com/"

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.83 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0"
    ]

    originStation = ""
    destinationStation = ""

    def __init__(self, headless=True):
        super().__init__(headless)

    def setupDriver(self):
        print("setting up webdriver")
        PROXY_HOST = "cw2homeproxy.ddns.net"  # Your DDNS hostname
        PROXY_PORT = "808"                   # Your CCProxy port
        PROXY_USER = "AICoursework2"       # Your CCProxy username
        PROXY_PASS = "INSERT PASSWORD HERE"
        options = webdriver.ChromeOptions()

        selenium_wire_options = {
            'proxy': {
                'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
                # CCProxy usually tunnels HTTPS over HTTP proxy
                'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
                'no_proxy': 'localhost,127.0.0.1'  # Bypass proxy for local addresses
            }
        }

        if self.headless:
            options.add_argument('--headless')
        options.add_argument("window-size=1920,1080")
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(
            "user-agent={random.choice(USER_AGENTS)}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"]) 
        options.add_experimental_option("useAutomationExtension", False) 

        try:
            service = Service(ChromeDriverManager().install())
            # When using selenium-wire, instantiate its WebDriver
            self.driver = webdriver.Chrome(
                service=service, options=options, seleniumwire_options=selenium_wire_options)
            print(f"webdriver (with selenium-wire for proxy) setup complete.")
            return self.driver
        except Exception as e:
            print(f"webdriver setup EXCEPTION: {e}")
            return None

    def searchJourneys(self, origin, destination, journeyDate, journeyTime, journeyType="single"):
        print(f"going from {origin} to {destination} on {
              journeyDate} at {journeyTime}")
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
        self.originStation = origin
        self.destinationStation = destination
        self.driver.get(self.websiteUrl)
        wait = WebDriverWait(self.driver, 20)
        
        time.sleep(random.uniform(1,2))
        # cookies again
        try:
            cookieAcceptButton = wait.until(
                EC.element_to_be_clickable(
                    ((By.ID, "close-banner-accept")))
            )
            cookieAcceptButton.click()
            print("accepted cookies")
        except Exception as e:
            print(f"error denying cookies: {e}")
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_cookie_error.png")

        # now we do origin and destination
        try:
            origin_input_selector = (
                By.CSS_SELECTOR, "div#autosuggest input.from-station-input")
            origin_field = wait.until(
                EC.visibility_of_element_located(origin_input_selector))
            origin_field.clear()
            origin_field.send_keys(origin)
            time.sleep(random.uniform(1, 2))
            origin_field.send_keys(Keys.TAB)
            print(f"entered origin {origin}")

            destination_input_selector = (
                By.CSS_SELECTOR, "div#to-station div#autosuggest input.to-station-input")
            destination_field = wait.until(
                EC.visibility_of_element_located(destination_input_selector))
            destination_field.clear()
            destination_field.send_keys(destination)
            time.sleep(random.uniform(1, 2))
            destination_field.send_keys(Keys.TAB)
            print(f"entered destination {destination}")
        except Exception as e:
            print(f"error in origin or destination picking: {e}")
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_origin_error.png")

        oneway_checkbox_label_xpath = "//label[contains(normalize-space(), 'One-way journey')]"
        oneway_checkbox_input_xpath = f"{
            oneway_checkbox_label_xpath}/input[@type='checkbox']"

        one_way_checkbox = wait.until(EC.presence_of_element_located(
            (By.XPATH, oneway_checkbox_input_xpath)))
        if not one_way_checkbox.is_selected():
            wait.until(EC.element_to_be_clickable(
                (By.XPATH, oneway_checkbox_label_xpath))).click()

        try:
            date_picker_trigger_selector = (
                By.CSS_SELECTOR, "div#date-picker-outbound div.input-button button.button")
            wait.until(EC.element_to_be_clickable(
                date_picker_trigger_selector)).click()
            print(f"clicked to open date/time picker dialog.")

            dialog_class_selector = "div.date-picker-dropdown"
            dialog_selector = (By.CSS_SELECTOR, dialog_class_selector)
            dialog_element = wait.until(
                EC.visibility_of_element_located(dialog_selector))
            print(f"date/time picker is open.")

            target_date_obj = datetime.strptime(journeyDate, "%d/%m/%Y")
            target_day_str = str(target_date_obj.day)
            target_month_year_display_str = target_date_obj.strftime(
                "%B %Y")

            month_year_display_selector = (
                By.CSS_SELECTOR, "div.ui-datepicker-title")
            prev_month_button_selector = (
                By.CSS_SELECTOR, "a.ui-datepicker-prev")
            next_month_button_selector = (
                By.CSS_SELECTOR, "a.ui-datepicker-next")

            retries = 12
            while retries > 0:
                current_month_year_element = dialog_element.find_element(
                    *month_year_display_selector)
                if target_month_year_display_str == current_month_year_element.text.strip():
                    print(
                        f"correct month/year visible: {target_month_year_display_str}")
                    break
                current_displayed_date_str = current_month_year_element.text.strip()
                try:
                    current_displayed_date_obj = datetime.strptime(
                        current_displayed_date_str, "%B %Y")
                    if target_date_obj < current_displayed_date_obj:
                        button_to_click = prev_month_button_selector
                        action_str = "previous"
                    else:
                        button_to_click = next_month_button_selector
                        action_str = "next"
                except ValueError:
                    print(f"could not parse current month display: {
                          current_displayed_date_str}. Defaulting to 'next'.")
                    button_to_click = next_month_button_selector
                    action_str = "next (fallback)"

                nav_button = dialog_element.find_element(*button_to_click)
                if "ui-state-disabled" in nav_button.get_attribute("class"):
                    print(f"datepicker '{
                          action_str}' month button is disabled. Cannot reach: {target_date_obj}")
                    return None
                nav_button.click()
                print(f"clicked {
                      action_str} month in datepicker.")
                time.sleep(random.uniform(1, 2.5))
                dialog_element = wait.until(
                    EC.visibility_of_element_located(dialog_selector))
                retries -= 1
            else:
                print(f"could not navigate to target month/year after 12 retries: {
                      target_month_year_display_str}")
                return None

            day_link_xpath = f".//table[@class='ui-datepicker-calendar']//td[@data-month='{
                target_date_obj.month-1}' and @data-year='{target_date_obj.year}']//a[text()='{target_day_str}']"
            day_element_to_click = dialog_element.find_element(
                By.XPATH, day_link_xpath)
            wait.until(EC.element_to_be_clickable(
                day_element_to_click)).click()
            print(f"clicked day: {target_day_str}")
            time.sleep(random.uniform(1, 2))

            target_hour_str = journeyTime[:2]
            target_minute_str = journeyTime[2:]

            hour_select_element = dialog_element.find_element(
                By.CSS_SELECTOR, "select.hours")
            Select(hour_select_element).select_by_visible_text(
                target_hour_str)  # Values might be same as text
            print(f"selected hour: {target_hour_str}")

            minute_select_element = dialog_element.find_element(
                By.CSS_SELECTOR, "select.minutes")
            Select(minute_select_element).select_by_visible_text(
                target_minute_str)
            print(f"selected minute: {target_minute_str}")
            time.sleep(random.uniform(1, 2))

            # click done button
            done_button_selector = (
                By.XPATH, "//div[@class='action-buttons']/button[contains(normalize-space(),'Done')]")
            wait.until(EC.element_to_be_clickable(
                done_button_selector)).click()
            print(f"clicked done in date/time dialog.")

            time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"error with the date and time: {e}")
            done_button_selector = (
                By.XPATH, "//div[@class='action-buttons']/button[contains(normalize-space(),'Done')]")
            wait.until(EC.element_to_be_clickable(
                done_button_selector)).click()

        # dateInputField = wait.until(
        #     EC.presence_of_element_located((By.CLASS_NAME, "date outdate")))
        # dateInputField.clear()
        # self.driver.execute_script("arguments[0].value = '';", dateInputField)
        # dateInputField.send_keys(journeyDate)
        
        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": random.choice(self.USER_AGENTS)})

        main_submit_button_selector = (
            By.CSS_SELECTOR, "button.btn.search.btn-primary")
        submit_button_element = wait.until(
            EC.element_to_be_clickable(main_submit_button_selector))
        self.driver.execute_script(
            "arguments[0].click();", submit_button_element)
        print(f"clicked main 'Find Tickets' button.")
        
        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": random.choice(self.USER_AGENTS)})
        
        #print(self.driver.execute_script("return navigator.userAgent;"))
        
        try:
            resultsUrlPart = "/results"
            wait.until(EC.url_contains(resultsUrlPart))
            initialResultsUrl = self.driver.current_url
        except:
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_search_error.png")
        self.driver.save_screenshot(
            f"debug/{self.websiteName.lower().replace(' ', '_')}_search_error.png")
        
        try_again_button_selector = (By.XPATH, "//a[contains(@class, 'btn-blue-normal') and text()='Try again?']")
        
        try:
            print("checking for try again button")
            try_again_button = WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable(try_again_button_selector))
            print("try again button found, clicking it")
            try_again_button.click()
            time.sleep(5)
        except:
            print("no try again button found")
        
        try:
            resultsGridID = "classic-grid"
            wait.until(EC.presence_of_element_located((By.ID, resultsGridID)))
            print("Found results grid!!")
        except:
            print("couldn't find results grid")
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_search_error.png")
        self.driver.save_screenshot(
            f"debug/{self.websiteName.lower().replace(' ', '_')}_search_error.png")
        
        time.sleep(random.uniform(1, 3))
        return self.driver.page_source

    def parseResults(self, pageHTML):
        print(f"parsing Trainsplit results from HTML...")
        if not pageHTML:
            print(f"no HTML content to parse.")
            return []

        soupParser = BeautifulSoup(pageHTML, 'html.parser')
        journeysData = []

        # find main grid container
        gridContainer = soupParser.find('div', class_='grid-container')
        if not gridContainer:
            print(f"cant find the main 'grid-container'.")
            return []

        timeCells = gridContainer.find_all('div', class_='time-cell')
        potentialJourneyElements = gridContainer.find_all(
            'div', recursive=False)
        i = 0
        while i < len(potentialJourneyElements):
            currentElement = potentialJourneyElements[i]

            # check if the current element is a time cell for an outward journey
            if 'time-cell' in currentElement.get('class', []) and \
               'return-time-cell' not in currentElement.get('class', []) and \
               currentElement.find('span', class_='journey-time'):
                timeCell = currentElement
                priceCell = None
                if (i + 1) < len(potentialJourneyElements) and \
                   'price-cell' in potentialJourneyElements[i+1].get('class', []):
                    priceCell = potentialJourneyElements[i+1]

                if timeCell and priceCell:
                    try:
                        departureTime = "N/A"
                        arrivalTime = "N/A"
                        changes = "N/A"
                        priceDisplay = "N/A"
                        priceNumeric = None
                        duration = "N/A"
                        journeyTimeSpan = timeCell.find(
                            'span', class_='journey-time')
                        if journeyTimeSpan:
                            timeText = journeyTimeSpan.get_text(
                                separator=" ", strip=True)
                            times = timeText.split('—')
                            if len(times) == 2:
                                departureTime = times[0].strip()
                                arrivalTime = times[1].strip()
                            elif len(times[0].split()) > 1:
                                parts = times[0].split()
                                if len(parts) >= 2:
                                    departureTime = parts[0]
                                    arrivalTime = parts[-1]

                        journeyTypeSmall = timeCell.find(
                            'small', class_='journey-type')
                        if journeyTypeSmall and journeyTypeSmall.find('a'):
                            changesText = journeyTypeSmall.find(
                                'a').get_text(strip=True)
                            match = re.search(
                                r'(\d+)\s*change', changesText, re.IGNORECASE)
                            if match:
                                changes = match.group(1)
                            elif "direct" in changesText.lower():
                                changes = "0"
                            else:
                                changes = changesText

                        priceSpan = priceCell.find('span')
                        if priceSpan:
                            priceDisplay = priceSpan.get_text(strip=True)
                            try:
                                priceNumeric = float(priceDisplay.replace(
                                    '£', '').replace('$', '').strip())
                            except ValueError:
                                print(f"can't get price: {
                                      priceDisplay}")

                        if departureTime != "N/A" and arrivalTime != "N/A":
                            try:
                                timeFormat = "%H:%M"
                                dtDep = datetime.strptime(
                                    departureTime, timeFormat)
                                dtArr = datetime.strptime(
                                    arrivalTime, timeFormat)
                                if dtArr < dtDep:
                                    dtArr += timedelta(days=1)
                                timeDiff = dtArr - dtDep
                                totalMinutes = int(
                                    timeDiff.total_seconds() / 60)
                                hours = totalMinutes // 60
                                minutes = totalMinutes % 60
                                if hours > 0:
                                    duration = f"{hours}h {minutes}m"
                                else:
                                    duration = f"{minutes}m"
                            except ValueError:
                                print(f"could not get times '{
                                      departureTime}', '{arrivalTime}' to calculate duration.")

                        journeysData.append({
                            'departureTime': departureTime,
                            'arrivalTime': arrivalTime,
                            'originStationName': self.originStation,
                            'destinationStationName': self.destinationStation,
                            'price': priceNumeric,
                            'priceDisplay': priceDisplay,
                            'duration': duration,
                            'changes': changes,
                        })
                        i += 1
                    except Exception as e_parse:
                        print(
                            f"error parsing a time/price cell pair: {e_parse}")
            i += 1

        if not journeysData:
            print(
                f"no journeys extracted from grid")
        else:
            print(f"parsed {
                  len(journeysData)} journeys from grid.")

        return journeysData
