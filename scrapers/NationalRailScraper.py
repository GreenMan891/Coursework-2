from .BaseScraper import BaseScraper
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


class NationalRailScraper(BaseScraper):
    websiteName = "National Rail"
    websiteUrl = "https://www.nationalrail.co.uk/"

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
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument("window-size=1920,1080")
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(
            "user-agent={random.choice(USER_AGENTS)}")

        service = Service(ChromeDriverManager().install())
        driverInstance = webdriver.Chrome(service=service, options=options)
        print("webdriver set up")
        return driverInstance

    def searchJourneys(self, origin, destination, journeyDate, journeyTime, journeyType="single"):
        print(f"going from {origin} to {destination} on {
              journeyDate} at {journeyTime}")
        self.driver.get(self.websiteUrl)
        wait = WebDriverWait(self.driver, 20)

        self.originStation = origin
        self.destinationStation = destination

        # first we accept cookies

        try:
            cookieDenyButton = wait.until(
                EC.element_to_be_clickable(
                    ((By.ID, "onetrust-accept-btn-handler")))
            )
            cookieDenyButton.click()
            print("cookie access accepted")
        except Exception as e:
            print(f"Cookie Banner not found or can't be clicked: {e}")
            pass

        # we press the swap button on national rail website

        try:
            planJouneyButtonSelector = "//button[@aria-label='Plan Your Journey']"
            planJouneyButton = wait.until(EC.element_to_be_clickable(
                (By.XPATH, planJouneyButtonSelector)))
            planJouneyButton.click()
        except Exception as e:
            print(f"could not click swap button {e}")

        # hopefully now that is pressed we can enter the rest

        originField = wait.until(
            EC.presence_of_element_located((By.ID, "jp-origin")))
        originField.clear()
        originField.send_keys(origin)
        time.sleep(0.5)
        originField.send_keys(Keys.TAB)
        print(f"entered origin {origin}")

        destinationField = wait.until(
            EC.presence_of_element_located((By.ID, "jp-destination")))
        destinationField.clear()
        destinationField.send_keys(destination)
        time.sleep(0.5)
        destinationField.send_keys(Keys.TAB)
        print(f"entered destination {destination}")

        try:
            dateFieldClick = wait.until(EC.element_to_be_clickable(
                (By.ID, "leaving-date")))
            dateFieldClick.click()
            dateFieldClick.clear()
        except Exception as e:
            print(f"can't click date field: {e}")
            self.driver.save_screenshot(
                f"debug/{self.websiteName.lower().replace(' ', '_')}_date_error.png")

        dateInputField = wait.until(
            EC.presence_of_element_located((By.ID, "leaving-date")))
        self.driver.execute_script("arguments[0].value = '';", dateInputField)
        dateInputField.clear()
        dateInputField.send_keys(Keys.CONTROL + "a")
        dateInputField.send_keys(Keys.DELETE)
        dateInputField.send_keys(journeyDate)
        print(f"entered date: {journeyDate}")

        self.driver.save_screenshot(
            f"debug/{self.websiteName.lower().replace(' ', '_')}_date_error.png")

        if len(journeyTime) == 4:
            hourTime = journeyTime[:2]
            minuteTime = journeyTime[2:]

            try:
                hourSelectElement = wait.until(
                    EC.presence_of_element_located((By.ID, "leaving-hour")))
                hourSelector = Select(hourSelectElement)

                hourSelector.select_by_value(hourTime)
                print(f"Selected Hour Time: {hourTime}")

                minuteSelectElement = wait.until(
                    EC.presence_of_element_located((By.ID, "leaving-min")))
                minuteSelector = Select(minuteSelectElement)

                minuteSelector.select_by_value(minuteTime)
                print(f"Selected Minute Time: {minuteTime}")
            except Exception as e:
                print(f"Error selecting dropdown time {e}")
        else:
            print(f"Error: journeyTime not in HHMM format")

        # try: ADULTS AND KIDS AND SINGLE AND RETURN CODE I DONT WANT
        #     adultsSelectElement = wait.until(
        #         EC.presence_of_element_located((By.ID, "adults")))
        #     adultsSelector = Select(adultsSelectElement)

        #     adultsSelector.select_by_value(numAdults)
        #     print(f"Num Adults Selected: {numAdults}")

        #     childrenSelectElement = wait.until(
        #         EC.presence_of_element_located((By.ID, "children")))
        #     childrenSelector = Select(childrenSelectElement)

        #     childrenSelector.select_by_value(numChildren)
        #     print(f"Num Children Selected: {numChildren}")
        # except Exception as e:
        #     print(f"Error selecting dropdown adults and kids {e}")

        # if journeyType.lower() == "single":
        #     singleButton = wait.until((EC.element_to_be_clickable(
        #         By.ID, "radio-jp-ticket-type-single")))
        #     singleButton.click()
        #     print("selected journey type single")
        # elif journeyType.lower() == "return":
        #     returnButton = wait.until((EC.element_to_be_clickable(
        #         By.ID, "radio-jp-ticket-type-return")))
        #     returnButton.click()

        submitButtonSelector = "//button[@aria-label='Get times and prices']"
        submitButton = wait.until(EC.element_to_be_clickable(
            (By.XPATH, submitButtonSelector)))
        # submitButton = wait.until((EC.element_to_be_clickable(By.ID, "button-jp")))
        submitButton.click()

        try:
            wait.until(EC.presence_of_element_located(
                (By.ID, "result-card-price-outward-0")))
            print("results page loaded")

        except Exception as e:
            print(f"Error, results page didnt load {e}")
            self.driver.save_screenshot("debugResultsError.png")

        return self.driver.page_source

    def parseResults(self, pageHTML):
        print("parsing journey results")
        if not pageHTML:
            print("no html content provided")
            return []

        soupParser = BeautifulSoup(pageHTML, 'html.parser')
        extractedJourneyData = []

        # find elements with class 'sc-80846f64'
        journeySections = soupParser.find_all(
            'section', class_='sc-80846f64-15')

        if not journeySections:
            print("no journey sections with that class")

        print(f"Found {len(journeySections)} journey sections to parse")

        for journeySection in journeySections:
            try:
                departureTime = "None"
                departureStation = "None"
                arrivalStation = "None"
                arrivalTime = "None"
                duration = "None"
                changes = "None"
                price = "None"
                isFastest = "None"

                # departure info
                departInfoDiv = journeySection.find(
                    'div', class_='sc-dabb4350-2')
                if departInfoDiv:
                    timeElement = departInfoDiv.find(
                        'time', class_='sc-5956bd38-9')
                    if timeElement:
                        departureTime = timeElement.get_text(strip=True)

                    stationSpan = departInfoDiv.find(
                        'span', class_='sc-f49d3fbe-3')
                    if stationSpan and stationSpan.find('span'):
                        departureStation = stationSpan.find(
                            'span').get_text(strip=True)
                        stationCodeSpan = stationSpan.find(
                            'span', class_='sc-f49d3fbe-4')
                        if stationCodeSpan:
                            departureStation += f" {
                                stationCodeSpan.get_text(strip=True)}"

                # arrival info
                arrivalInfoDiv = journeySection.find(
                    'div', class_='sc-dabb4350-4')
                if arrivalInfoDiv:
                    timeElement = departInfoDiv.find(
                        'time', class_='sc-5956bd38-9')
                    if timeElement:
                        departureTime = timeElement.get_text(strip=True)

                    stationSpan = arrivalInfoDiv.find(
                        'span', class_='sc-f49d3fbe-3')
                    if stationSpan and stationSpan.find('span'):
                        arrivalStation = stationSpan.find(
                            'span').get_text(strip=True)
                        stationCodeSpan = stationSpan.find(
                            'span', class_='sc-f49d3fbe-4')
                        if stationCodeSpan:
                            arrivalStation += f" {
                                stationCodeSpan.get_text(strip=True)}"

                # getting duration and syntax
                durationChangesP = journeySection.find(
                    'p', class_='sc-5956bd38-7')
                if durationChangesP:
                    timeTag = durationChangesP.find('time')
                    if timeTag and timeTag.find('span', attrs={'aria-hidden': 'true'}):
                        duration = timeTag.find('span', attrs={
                                                'aria-hidden': 'true'}).get_text(strip=True).replace(',', '').strip()

                    lastSpanInP = durationChangesP.find_all(
                        'span')[-1] if durationChangesP.find_all('span') else None
                    if lastSpanInP:
                        changesText = lastSpanInP.get_text(strip=True)
                        if changesText.lower() == "direct":
                            changes = "0 changes (Direct)"
                        else:
                            changes = changesText

                # getting the price
                priceDiv = journeySection.find('div', class_='sc-80846f64-2')
                priceDisplay = "N/A"  # For storing the string like "£70.10"
                priceNumeric = None  # For storing the float like 70.10

                if priceDiv and len(priceDiv.find_all('span')) == 2:
                    priceDisplay = priceDiv.find_all(
                        'span')[1].get_text(strip=True)
                    try:
                        # Attempt to convert to float here
                        priceNumeric = float(priceDisplay.replace(
                            '£', '').replace('$', '').strip())
                    except ValueError:
                        print(f"could not parse price string '{
                              priceDisplay}' to float.")
                        priceNumeric = None  # Ensure it's None if conversion fails

                # fastest journey
                fastestTagSpan = journeySection.find(
                    'span', class_='sc-80846f64-17')
                if fastestTagSpan and "Fastest" in fastestTagSpan.get_text():
                    isFastest = True
                else:
                    isFastest = False

                journeyDetails = {
                    "departureTime": departureTime,
                    "departureStation": self.originStation,
                    "arrivalStation": self.destinationStation,
                    "arrivalTime": arrivalTime,
                    "duration": duration,
                    "changes": changes,
                    "price": priceNumeric,
                    "priceDisplay": priceDisplay,
                    "isFastest": isFastest
                }
                extractedJourneyData.append(journeyDetails)
            except Exception as e:
                print(f"error parsing part of the journey from the html: {e}")
                continue
        if not extractedJourneyData:
            print("journey data extraction failed")
        return extractedJourneyData

    # def findCheapestJourney(journeyList):
    #     if not journeyList:
    #         print("couldnt find journeylist")

    #     cheapestJourney = None
    #     lowestPrice = 10000000  # super high number for later

    #     for journey in journeyList:
    #         priceStr = journey.get("price", "None").replace(
    #             '£', '').replace('$', '').strip()
    #         try:
    #             currentPrice = float(priceStr)
    #             if currentPrice < lowestPrice:
    #                 lowestPrice = currentPrice
    #                 cheapestJourney = journey
    #         except ValueError:
    #             print("can't find the price of a journey")

    #     return cheapestJourney
