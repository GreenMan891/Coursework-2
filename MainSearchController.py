import argparse
from datetime import datetime
from scrapers.NationalRailScraper import NationalRailScraper
from scrapers.GreaterAngliaScraper import GreaterAngliaScraper
from utils import cleanPrice


def findCheapestOverall(allProviderJourneys):
    cheapestJourney = None
    lowestPrice = 10000000

    if not allProviderJourneys:
        return None

    for journey in allProviderJourneys:
        currentPriceNumeric = journey.get("price")

        if currentPriceNumeric is not None:
            try:
                currentPrice = float(currentPriceNumeric)
                if currentPrice < lowestPrice:
                    lowestPrice = currentPrice
                    cheapestJourney = journey
            except (ValueError, TypeError):
                print(f"could not convert price '{
                      currentPriceNumeric}' to float from {journey.get('sourceWebsite')}.")
                continue
        else:
            print("currentpricenumeric is none")
    return cheapestJourney


def main():
    parser = argparse.ArgumentParser(
        description="Find the cheapest train ticket from multiple providers")
    parser.add_argument("origin", help="Origin station: ")
    parser.add_argument("destination", help="Destination station: ")
    parser.add_argument("date", help="Journey date (DD/MM/YYYY): ")
    parser.add_argument(
        "time", help="Journey time (HHMM, e.g., 0930 for 9:30 AM): ")
    parser.add_argument("--headless", action="store_true",
                        help="Run browsers in headless mode.")

    args = parser.parse_args()

    allScrapers = [
        NationalRailScraper,
        GreaterAngliaScraper
    ]  # when we make more rail scrapers add them here

    allJourneysFound = []

    for ScraperClass in allScrapers:
        scraperInstance = ScraperClass(headless=args.headless)
        print(f"\n currently checking {scraperInstance.websiteName}")
        providerJourneys = scraperInstance.getCheapestJourney(
            args.origin,
            args.destination,
            args.date,
            args.time
        )
        if providerJourneys:
            allJourneysFound.extend(providerJourneys)
            print(f"found {len(providerJourneys)} options from {
                  scraperInstance.websiteName}")
        else:
            print(f"No journeys found, might be an error with {
                  scraperInstance.websiteName}")

    if not allJourneysFound:
        print("\n no train journeys from any provider with these arguements")
        return

    print(f"\n found {len(allJourneysFound)} journeys IN TOTAL")

    overallCheapest = findCheapestOverall(allJourneysFound)

    if overallCheapest:
        print("\n cheapest ticket found!!")
        print(f"  provider: {overallCheapest.get('sourceWebsite')}")
        print(f"  origin: {args.origin}")
        print(f"  destination: {args.destination}")
        print(f"  departure Time: {
              overallCheapest.get('departureTime', 'N/A')}")
        print(f"  arrival Time: {overallCheapest.get('arrivalTime', 'N/A')}")
        price_display_to_show = overallCheapest.get('priceDisplay')
        if not price_display_to_show and overallCheapest.get('price') is not None:
            try:
                price_display_to_show = f"£{
                    float(overallCheapest.get('price')):.2f}"
            except (ValueError, TypeError):
                price_display_to_show = "N/A (error formatting price)"
        elif not price_display_to_show:
            price_display_to_show = "N/A"

        print(f"  price: {price_display_to_show}")
        print(f"  duration: {overallCheapest.get('duration', 'N/A')}")
        print(f"  changes: {overallCheapest.get('changes', 'N/A')}")
        print(f"  Book via: {overallCheapest.get('bookingLink')}")


if __name__ == "__main__":
    main()
