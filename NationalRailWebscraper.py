from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json
import requests
from datetime import datetime, timedelta

url = "https://www.nationalrail.co.uk/"


def setupWebDriver():
    print("setting up webdriver")
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    service = Service(ChromeDriverManager().install())
    driverInstance = webdriver.Chrome(service=service, options=options)
    print("webdriver set up")
    return driverInstance


def trainSearch(webDriver, origin, destination, journeyDate, journeyTime, numAdults, numChildren, journeyType="single"):
    print(f"going from {origin} to {destination} on {
          journeyDate} at {journeyTime}")
    webDriver.get(url)
    wait = WebDriverWait(webDriver, 20)

    # first we accept cookies

    try:
        cookieDenyButton = wait.until(
            EC.element_to_be_clickable(
                ((By.ID, "onetrust-accept-btn-handler")))
        )
        cookieDenyButton.click()
        print("cookie access denied")
    except Exception as e:
        print(f"Cookie Banner not found or can't be clicked: {e}")
        pass

    # we press the swap button on national rail website

    try:
        planJouneyButtonSelector = "//button[@aria-label='Plan Your Journey']"
        planJouneyButton = wait.until(EC.element_to_be_clickable(
            (By.XPATH, planJouneyButtonSelector)))
        planJouneyButton.click()
        # swapButton = wait.until(EC.element_to_be_clickable((
        #     By.ID, "jp-preview-toggle-button")))
        # swapButton.click()
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
    except Exception as e:
        print(f"can't click date field {e}")

    dateInputField = wait.until(
        EC.presence_of_element_located((By.ID, "leaving-date")))
    webDriver.execute_script("arguments[0].value = '';", dateInputField)
    dateInputField.send_keys(journeyDate)
    print(f"entered date: {journeyDate}")

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

    # try:
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
        webDriver.save_screenshot("debugResultsError.png")

    return webDriver.page_source


def parseJourneyResults(pageHTML):
    print("parsing journey results")
    if not pageHTML:
        print("no html content provided")
        return []

    soupParser = BeautifulSoup(pageHTML, 'html.parser')
    extractedJourneyData = []

    # find elements with class 'sc-80846f64'
    journeySections = soupParser.find_all('section', class_='sc-80846f64-15')

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
            departInfoDiv = journeySection.find('div', class_='sc-dabb4350-2')
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
            arrivalInfoDiv = journeySection.find('div', class_='sc-dabb4350-4')
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
            durationChangesP = journeySection.find('p', class_='sc-5956bd38-7')
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
            if priceDiv and len(priceDiv.find_all('span')) == 2:
                price = priceDiv.findAll('span')[1].get_text(
                    strip=True)  # convert to int later

            # fastest journey
            fastestTagSpan = journeySection.find(
                'span', class_='sc-80846f64-17')
            if fastestTagSpan and "Fastest" in fastestTagSpan.get_text():
                isFastest = True
            else:
                isFastest = False

            journeyDetails = {
                "departureTime": departureTime,
                "departureStation": departureStation,
                "arrivalStation": arrivalStation,
                "arrivalTime": arrivalTime,
                "duration": duration,
                "changes": changes,
                "price": price,
                "isFastest": isFastest
            }
            extractedJourneyData.append(journeyDetails)
        except Exception as e:
            print(f"error parsing part of the journey from the html: {e}")
            continue
    if not extractedJourneyData:
        print("journey data extraction failed")
    return extractedJourneyData
    # jsonLdScripts = soupParser.find_all('script', type='application/ld+json')
    # foundViaJsonLd = False
    # print(f"found {len(jsonLdScripts)} json script tags")
    # nextDataScript = soupParser.find(
    #     'script', id='__NEXT_DATA__', type='application/json')
    # if nextDataScript and nextDataScript.string:
    #     print("found next data script tag. parsing now")
    #     import json

    #     try:
    #         nextDataJson = json.loads(nextDataScript.string)
    #         print(nextDataJson)
    #     except Exception as e:
    #         print("can't load nextdata")

    # except Exception:
    #     pass
    # for scriptTag in jsonLdScripts:
    #     import json

    #     try:
    #         jsonData = json.loads(scriptTag.string)
    #         itemsToCheck = []
    #         if isinstance(jsonData, list):


def findCheapestJourney(journeyList):
    if not journeyList:
        print("couldnt find journeylist")

    cheapestJourney = None
    lowestPrice = 10000000  # super high number for later

    for journey in journeyList:
        priceStr = journey.get("price", "None").replace(
            '£', '').replace('$', '').strip()
        try:
            currentPrice = float(priceStr)
            if currentPrice < lowestPrice:
                lowestPrice = currentPrice
                cheapestJourney = journey
        except ValueError:
            print("can't find the price of a journey")

    return cheapestJourney


if __name__ == "__main__":
    webDriver = None

    try:
        webDriver = setupWebDriver()
        futureDate = datetime.now() + timedelta(days=7)
        searchDate = futureDate.strftime("%d %b %Y")

        origin = "Norwich"
        destination = "London"
        timeOfJourney = "1630"

        numAdults = 1
        numChildren = 0

        resultsHTML = trainSearch(
            webDriver, origin, destination, searchDate, timeOfJourney, numAdults, numChildren)

        if resultsHTML:
            with open("results_page.html", "w", encoding="utf-8") as f:
                f.write(webDriver.page_source)
            print("saved results page")

            allJourneys = parseJourneyResults(webDriver.page_source)

            if allJourneys:
                print(f"found {len(allJourneys)} Journeys")
                for i, journeyData in enumerate(allJourneys):
                    print(f"\nJourney {i+1}:")
                    for key, value in journeyData.items():
                        formattedKey = ' '.join(word.capitalize()
                                                for word in key.split('_'))
                        print(f"  {formattedKey}: {value}")
                cheapestJourney = findCheapestJourney(allJourneys)
                if cheapestJourney:
                    print("\n CHEAPEST JOURNEY")
                    for key, value in cheapestJourney.items():
                        formattedKey = key.replace('_', ' ').title()
                        print(f"  {formattedKey}: {value}")
            else:
                print("no journey data was found")

    except Exception as e:
        print(f"\n--- AN UNEXPECTED ERROR OCCURRED ---")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        if webDriver:
            try:
                webDriver.save_screenshot("critical_error_screenshot.png")
                print("saved screenshot: critical_error_screenshot.png")
            except:
                print("could not save screenshot")
    finally:
        if webDriver:
            print("\n scraper finished closing webdriver in 3 seconds.")
            time.sleep(3)
            webDriver.quit()
            print("WebDriver closed.")
