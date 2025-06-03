from abc import ABC, abstractmethod


class BaseScraper(ABC):
    # abstract class for all other scrapers
    websiteName = ""
    websiteUrl = ""
    USER_AGENTS = []

    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None  # set up in setupDriver

    @abstractmethod
    def setupDriver(self):
        # sets up selenium webdriver for this site
        pass

    @abstractmethod
    def searchJourneys(self, originStation, destinationStation, journeyDate, journeyTime, journeyType="single"):
        # performs the journey search
        pass

    @abstractmethod
    def parseResults(self, HTML):
        # reads the HTML content from the result page
        # returns with a list of journeys each in a dictionary
        pass

    def getCheapestJourney(self, originStation, destinationStation, journeyDate, journeyTime, journeyType="single"):
        pageHTML = None
        journeys = []
        try:
            self.driver = self.setupDriver()
            if not self.driver:
                print(f" driver setup failed.")
                return []

            pageHTML = self.searchJourneys(
                originStation, destinationStation, journeyDate, journeyTime)

            if pageHTML:
                with open(f"debug/{self.websiteName.lower().replace(' ', '_')}_results.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print(
                    f"saved HTML of results page")

                journeys = self.parseResults(self.driver.page_source)
            else:
                print(f"couldnt get page HTML from search")
        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            import traceback
            traceback.print_exc()
            if self.driver:
                try:
                    self.driver.save_screenshot(
                        f"debug/{self.websiteName.lower().replace(' ', '_')}_error.png")
                except:
                    pass
        finally:
            if self.driver:
                self.driver.quit()
                print(f"webbriver closed")
            self.driver = None

        for journey in journeys:
            journey['sourceWebsite'] = self.websiteName
            journey['bookingLink'] = self.websiteUrl
        return journeys

    def quitDriver(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
