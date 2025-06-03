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
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import random


class GreaterAngliaScraper(BaseScraper):
    websiteName = "Greater Anglia"
    websiteUrl = "https://www.greateranglia.co.uk/"

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

        # cookies again
        try:
            cookieAcceptButton = wait.until(
                EC.element_to_be_clickable(
                    ((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")))
            )
            cookieAcceptButton.click()
            print("accepted cookies")
        except Exception as e:
            print(f"error denying cookies: {e}")
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_cookie_error.png")

        # now we do origin and destination
        try:
            originField = wait.until(
                EC.presence_of_element_located((By.ID, "from-buy-header")))
            originField.clear()
            originField.send_keys(origin)
            time.sleep(random.uniform(0.5, 1))
            originField.send_keys(Keys.TAB)
            print(f"entered origin {origin}")

            destinationField = wait.until(
                EC.presence_of_element_located((By.ID, "to-header")))
            destinationField.clear()
            destinationField.send_keys(destination)
            time.sleep(random.uniform(0.4, 1))
            destinationField.send_keys(Keys.TAB)
            print(f"entered destination {destination}")

            # dateInputField = wait.until(
            #     EC.presence_of_element_located((By.CLASS_NAME, "date outdate")))
            # dateInputField.clear()
            # self.driver.execute_script("arguments[0].value = '';", dateInputField)
            # dateInputField.send_keys(journeyDate)

        except Exception as e:
            print(f"error in origin or destination picking: {e}")
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_origin_error.png")

        submitButtonSelector = "button.submit.btn[type='submit']"
        time.sleep(random.uniform(0.8, 1.5))
        submitButton = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, submitButtonSelector)))
        submitButton.click()

        try:
            resultsUrlPart = "/book/results"
            wait.until(EC.url_contains(resultsUrlPart))
            initialResultsUrl = self.driver.current_url
        except:
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_search_error.png")
        
        time.sleep(random.uniform(2,4))
        parsedUrl = urlparse(initialResultsUrl)
        # parse_qs returns values as lists
        queryParams = parse_qs(parsedUrl.query)

        try:
            dateObj = datetime.strptime(journeyDate, "%d/%m/%Y")
            formattedTargetDate = dateObj.strftime("%Y-%m-%d")
            rawTime = f"{journeyTime[:2]}:{journeyTime[2:]}:00"
            targetOutwardDatetime = f"{formattedTargetDate}T{
                rawTime}"
        except ValueError:
            print(
                f"[{self.websiteName}] Invalid target date/time format: {journeyDate}, {journeyTime}")
            return None

        queryParams['outwardDate'] = [targetOutwardDatetime]
        queryParams['outwardDateType'] = [
            'departAfter']
        queryParams['journeySearchType'] = [
            journeyType.lower()]

        queryParams.pop('selectedOutward', None)
        queryParams.pop('bookingToken', None)

        newQueryString = urlencode(queryParams, doseq=True)
        modifiedUrlParts = list(parsedUrl)
        modifiedUrlParts[4] = newQueryString
        finalSearchUrl = urlunparse(modifiedUrlParts)

        self.driver.get(finalSearchUrl)
        time.sleep(random.uniform(1.8, 2.5))
        try:
            cookieAcceptButton = wait.until(
                EC.element_to_be_clickable(
                    ((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll")))
            )
            cookieAcceptButton.click()
            print("accepted cookies for the second time")
        except Exception as e:
            print(f"error accepting cookies for the second time: {e}")
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_cookie_error.png")
        time.sleep(random.uniform(1.8, 2.5))
        return self.driver.page_source

    def parseResults(self, pageHTML):
        if not pageHTML:
            print(f"[{self.websiteName}] No HTML content to parse.")
            return []

        soupParser = BeautifulSoup(pageHTML, 'html.parser')
        journeysData = []

        main_ul = soupParser.find(
            'ul', class_='ColumnContent-module__alternativesListWrapper__YSLNb')
        journeyItemsSource = []

        if main_ul:
            journeyItemsSource = [
                li for li in main_ul.find_all('li', recursive=False)
                if li.find('div', class_='_1rn4jd0k')
            ]
            if not journeyItemsSource:
                print(
                    f"[{self.websiteName}] No direct <li> children with journey structure found in main UL.")

        if not journeyItemsSource:
            print(
                f"[{self.websiteName}] main UL not found or empty. Trying fallback to find all relevant LIs.")
            allListItems = soupParser.find_all('li')
            journeyItemsSource = [
                li for li in allListItems if li.find('div', class_='_1rn4jd0k')]

        if not journeyItemsSource:
            print(f"[{self.websiteName}] no journey list items found by any method.")
            return []

        print(f"[{self.websiteName}] found {
              len(journeyItemsSource)} potential journey items to parse.")

        for item_idx, item_li in enumerate(journeyItemsSource):
            print(f" processing item {item_idx + 1}")
            try:
                departureTime = "N/A"
                arrivalTime = "N/A"
                duration = "N/A"
                changes = "N/A"
                standardPriceDisplay = "N/A"
                standardPriceNumeric = None

                depTimeDiv = item_li.find(
                    'div', attrs={'data-test': 'train-results-departure-time'})
                if depTimeDiv:
                    timeTag = depTimeDiv.find(
                        'time', attrs={'data-test': 'machine-readable'})
                    if timeTag and timeTag.find('span', attrs={'aria-hidden': 'true'}):
                        departureTime = timeTag.find(
                            'span', attrs={'aria-hidden': 'true'}).get_text(strip=True)

                arrTimeDiv = item_li.find(
                    'div', attrs={'data-test': 'train-results-arrival-time'})
                if arrTimeDiv:
                    timeTag = arrTimeDiv.find(
                        'time', attrs={'data-test': 'machine-readable'})
                    if timeTag and timeTag.find('span', attrs={'aria-hidden': 'true'}):
                        arrivalTime = timeTag.find(
                            'span', attrs={'aria-hidden': 'true'}).get_text(strip=True)

                durationChangesDiv = item_li.find(
                    'div', attrs={'data-test': 'desktop-duration-and-changes'})
                if durationChangesDiv:
                    durationSpan = durationChangesDiv.find(
                        'span',
                        lambda tag: isinstance(tag, type(soupParser.new_tag("span"))) and
                        tag.has_attr('aria-hidden') and
                        # Simpler check for duration
                        'm' in tag.get_text(strip=True)
                    )
                    if durationSpan:
                        duration = durationSpan.get_text(strip=True)

                    changesButton = durationChangesDiv.find(
                        'button', class_='_1qhx8f7NaN')
                    if changesButton and changesButton.find('span'):
                        changes = changesButton.find(
                            'span').get_text(strip=True)
                else:
                    print(
                        f"[{self.websiteName}] duration or changes div not found for item {item_idx + 1}")
                    # print(item_li.prettify())

                priceOptionsFieldset = item_li.find(
                    'fieldset', class_='style-module__root__tyWHA')
                if priceOptionsFieldset:
                    standardFareInput = priceOptionsFieldset.find(
                        'input', attrs={'data-test': 'standard-class-price-radio-btn'})
                    priceSourceElement = None
                    if standardFareInput:
                        labelForStandard = priceOptionsFieldset.find(
                            'label', attrs={'for': standardFareInput.get('id')})
                        if labelForStandard:
                            priceSourceElement = labelForStandard.find(
                                'div', attrs={'data-test': 'alternative-price'})
                    else:
                        priceSourceElement = priceOptionsFieldset.find(
                            'div', attrs={'data-test': 'alternative-price'})

                    if priceSourceElement:
                        priceSpanWrapper = priceSourceElement.find(
                            'span', class_='_1b1fkvke')
                        if priceSpanWrapper:
                            finalPriceSpan = priceSpanWrapper.find(
                                'span', class_='style-module__root__c26ye')
                            if finalPriceSpan:
                                standardPriceDisplay = finalPriceSpan.get_text(
                                    strip=True)
                                try:
                                    standardPriceNumeric = float(
                                        standardPriceDisplay.replace('£', '').replace('$', '').strip())
                                except ValueError:
                                    print(f"          VALUE_ERROR parsing price: '{
                                          standardPriceDisplay}' for item {item_idx + 1}")
                                    standardPriceNumeric = None
                journeysData.append({
                    'departureTime': departureTime,
                    'arrivalTime': arrivalTime,
                    'originStationName': self.originStation,
                    'destinationStationName': self.destinationStation,
                    'price': standardPriceNumeric,
                    'priceDisplay': standardPriceDisplay,
                    'duration': duration,
                    'changes': changes,
                })

            except Exception as e:
                print(f"[{self.websiteName}] error parsing a journey item (idx {
                      item_idx}) from HTML: {e}")
                # import traceback for debugging
                # traceback.print_exc()
                # # print(item_li.prettify())
                continue

        if not journeysData:
            print(
                f"[{self.websiteName}] No journeys extracted. Check parsing logic and HTML structure.")
        else:
            print(f"[{self.websiteName}] Successfully parsed {
                  len(journeysData)} journeys.")
        return journeysData
