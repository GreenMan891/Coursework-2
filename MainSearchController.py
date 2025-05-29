import argparse
from datetime import datetime
from scrapers.NationalRailScraper import NationalRailScraper
from scrapers.GreaterAngliaScraper import GreaterAngliaScraper
import json
import os
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
    parser.add_argument("--output_file", default="searchResults.json",
                    help="Filename for the JSON output (default: searchResults.json)")

    args = parser.parse_args()

    outputData = {
        "search_parameters": {
            "origin": args.origin,
            "destination": args.destination,
            "date": args.date,
            "time": args.time
        },
        "allJourneysCount": 0,
        "cheapestJourney": None,
        "statusMessages": []
    }
    
    outputDir = "output" 
    if not os.path.exists(outputDir):
        try:
            os.makedirs(outputDir)
            print(f"created directory: {outputDir}")
        except OSError as e:
            print(f"error creating directory {outputDir}: {e}. output will be in current directory.")
            output_dir = "." # Fallback to current directory

    outputJsonFilePath = os.path.join(outputDir, args.output_file)

    allScrapers = [
        NationalRailScraper,
        GreaterAngliaScraper
    ]  # when we make more rail scrapers add them here

    allJourneysFound = []

    for ScraperClass in allScrapers:
        scraperInstance = ScraperClass(headless=args.headless)
        print(f"\n currently checking {scraperInstance.websiteName}")
        outputData["statusMessages"].append(
            f" currently checking {scraperInstance.websiteName}...")

        providerJourneys = scraperInstance.getCheapestJourney(
            args.origin,
            args.destination,
            args.date,
            args.time
        )
        if providerJourneys:
            allJourneysFound.extend(providerJourneys)
            foundMsg = f"found {len(providerJourneys)} options from {scraperInstance.websiteName}"
            print(foundMsg)
            outputData["statusMessages"].append(foundMsg)
        else:
            notFoundMsg = f"No journeys found, might be an error with {scraperInstance.websiteName}"
            print(notFoundMsg)
            outputData["statusMessages"].append(notFoundMsg)
    
    outputData["allJourneysCount"] = len(allJourneysFound)

    if not allJourneysFound:
        no_results_msg = "no train journeys found from any provider with these arguments."
        print(f"\n{no_results_msg}")
        outputData["statusMessages"].append(no_results_msg)
        return

    print(f"\n found {len(allJourneysFound)} journeys IN TOTAL")

    overallCheapest = findCheapestOverall(allJourneysFound)

    if overallCheapest:
        print("\n cheapest ticket found!!")
        
        cheapestJourneyJson = {
        "provider": overallCheapest.get('sourceWebsite'),
        "originStation": overallCheapest.get('originStationName', args.origin),
        "destinationStation": overallCheapest.get('destinationStationName', args.destination),
        "departureTime": overallCheapest.get('departureTime', 'N/A'),
        "arrivalTime": overallCheapest.get('arrivalTime', 'N/A'),
        "priceDisplay": overallCheapest.get('priceDisplay', 'N/A'),
        "priceNumeric": overallCheapest.get('price'),
        "duration": overallCheapest.get('duration', 'N/A'),
        "changes": overallCheapest.get('changes', 'N/A'),
        "bookingLink": overallCheapest.get('bookingLink', 'N/A')
        }
        outputData["cheapestJourney"] = cheapestJourneyJson
        outputData["statusMessages"].append("found the cheapest journey.")
    else:
        noCheapestMsg = "could not determine an overall cheapest ticket, error has occured"
        print(f"\n{noCheapestMsg}")
        outputData["statusMessages"].append(noCheapestMsg)
    
    print("\n json output:")
    print(json.dumps(outputData, indent=4, sort_keys=True))
    
    try:
        with open(outputJsonFilePath, 'w', encoding='utf-8') as f:
            json.dump(outputData, f, ensure_ascii=False, indent=4, sort_keys=True)
            print(f"\nJSON output successfully saved to: {outputJsonFilePath}")
    except IOError as e:
        print(f"\nError saving JSON output to file {outputJsonFilePath}: {e}")
    
    


if __name__ == "__main__":
    main()
