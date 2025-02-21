"""Functions for extracting emails from websites."""

import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from email_validator import validate_email, EmailNotValidError


def is_valid_email(email: str) -> str:
    """Validate and normalize an email address using email-validator.

    Args:
        email (str): The email address to validate.

    Returns:
        str: A normalized email address if valid, otherwise None.
    """
    try:
        # check_deliverability=False flag avoids DNS lookups.
        valid = validate_email(email, check_deliverability=False)
        return valid.email
    except EmailNotValidError:
        return None


def get_emails_from_website(url: str) -> list:
    """Get emails from a website and its contact page.

    Args:
        url (str): The URL of the website.

    Returns:
        list: A list of emails found on the website and its contact page.
    """
    emails = set()

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        main_page = response.text
    except Exception as e:
        print(f"Error fetching main page '{url}': {e}")
        main_page = ""

    if main_page:
        try:
            potential_main_email_candidates = set(
                re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", main_page)
            )

            for candidate in potential_main_email_candidates:
                valid = is_valid_email(candidate)
                if valid:
                    emails.add(valid)
        except Exception as e:
            print(f"Error extracting emails from main page '{url}': {e}")

        try:
            soup = BeautifulSoup(main_page, "html.parser")
        except Exception as e:
            print(f"Error parsing HTML from '{url}': {e}")
            soup = None

        if soup:
            contact_links = set()
            for link in soup.find_all("a", href=True):
                href = link["href"]

                if href.lower().startswith("mailto:"):
                    potential_email = href.split("mailto:")[1]

                    valid = is_valid_email(potential_email)
                    if valid:
                        emails.add(valid)

                elif "kontakt" in href.lower() or "impressum" in href.lower():
                    contact_links.add(href)

            for href in contact_links:
                contact_url = urljoin(url, href)
                try:
                    contact_response = requests.get(contact_url, timeout=30)
                    contact_response.raise_for_status()
                    contact_page = contact_response.text

                    potential_contact_email_candidates = set(
                        re.findall(
                            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                            contact_page,
                        )
                    )
                    for candidate in potential_contact_email_candidates:
                        valid = is_valid_email(candidate)
                        if valid:
                            emails.add(valid)

                except Exception as e:
                    print(
                        f"Error fetching or processing contact page '{contact_url}': {e}"
                    )

    return list(emails)
