"""This script queries the Google Places API for a list of keywords and saves the results in a file.

Docs:
    https://developers.google.com/maps/documentation/places/web-service/text-search?hl=de
"""

import os
import requests
import pandas as pd
import dotenv
from keywords import keywords

dotenv.load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


results = []
for keyword in keywords:
    print(f"Searching for: {keyword}")

    try:
        response = requests.post(
            url="https://places.googleapis.com/v1/places:searchText",
            params={
                "textQuery": keyword,
                "languageCode": "de",
                "pageSize": 50,
            },
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": API_KEY,
                "X-Goog-FieldMask": "*",  # This returns all available fields.
            },
            timeout=60,
        )

        response.raise_for_status()
        data = response.json()

        places: list[dict] = data["places"]
        for place in places:
            phone_number = place.get("internationalPhoneNumber", "")
            address = place.get("formattedAddress", "")
            website_uri = place.get("websiteUri", "")
            place_type = place.get("primaryType", "")

            results.append(
                {
                    "name": place["name"],
                    "phone_number": phone_number,
                    "address": address,
                    "website_uri": website_uri,
                    "place_type": place_type,
                }
            )

    except Exception as e:
        print(f"Error querying '{keyword}': {e}")

# Deduplicate results based on address and website_uri
unique_results = {}
for result in results:
    key = (result["address"], result["website_uri"])
    unique_results[key] = result

print(f"Found {len(unique_results)} unique results.")

df = pd.DataFrame(list(unique_results.values()))

excel_datei = "zahnarzt_frankfurt.xlsx"
df.to_excel(excel_datei, index=False)
print(f"Excel saved as {excel_datei}")
