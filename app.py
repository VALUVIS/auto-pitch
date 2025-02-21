"""This script queries the Google Places API for a list of keywords and saves the results in a file.

Docs:
    https://developers.google.com/maps/documentation/places/web-service/text-search?hl=de
"""

import streamlit as st
import os
import requests
import pandas as pd
import dotenv
import io

dotenv.load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    st.error(
        "Google Maps API key not found. Please set the environment variable 'GOOGLE_MAPS_API_KEY'."
    )
    st.stop()

PASSWORD = os.getenv("PASSWORD")
password_input = st.text_input("Enter Password", type="password")
if password_input != PASSWORD:
    st.warning("Please enter the correct password to access the application.")
    st.stop()

st.title("Google Places API Query Tool")
st.markdown(
    """
This tool queries the Google Places API for a list of keywords and outputs the results as an Excel download.
Please enter one keyword per line.
"""
)

keywords_input = st.text_area("Enter Keywords", height=150)

if st.button("Run Query"):
    if not keywords_input.strip():
        st.error("Please provide at least one keyword.")
    else:
        keywords = [kw.strip() for kw in keywords_input.splitlines() if kw.strip()]
        results = []
        for keyword in keywords:
            st.write(f"Searching for: **{keyword}**")
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

                # Extract places data; if no key exists, use an empty list.
                places = data.get("places", [])
                for place in places:
                    results.append(
                        {
                            "name": place.get("name", ""),
                            "phone_number": place.get("internationalPhoneNumber", ""),
                            "address": place.get("formattedAddress", ""),
                            "website_uri": place.get("websiteUri", ""),
                            "place_type": place.get("primaryType", ""),
                        }
                    )
            except Exception as e:
                st.error(f"Error querying '{keyword}': {e}")

        unique_results = {}
        for result in results:
            key = (result["address"], result["website_uri"])
            unique_results[key] = result

        st.write(f"Found **{len(unique_results)}** unique results.")
        df = pd.DataFrame(list(unique_results.values()))

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
            worksheet = writer.sheets["Sheet1"]
            worksheet.set_column("A:E", 30)
        output.seek(0)

        st.download_button(
            label="Download Excel",
            data=output,
            file_name="places_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
