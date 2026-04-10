import requests
from bs4 import BeautifulSoup
import time

OPTCG_BASE_URL = "https://en.onepiece-cardgame.com/cardlist/?series="
OPTCG_CODE_PREFIX = "569"
PREMIUM_BOOSTERS = 2
EXTRA_BOOSTERS = 3
REGULAR_SETS = 14
STARTER_DECKS = 29

def build_card_set_codes():
    set_codes = {}
    for i in range(PREMIUM_BOOSTERS):
        set_codes[f"PRB{i+1:02d}"] = f"{OPTCG_CODE_PREFIX}{300 + i+1:03d}"
    for i in range(EXTRA_BOOSTERS):
        set_codes[f"EB{i+1:02d}"] = f"{OPTCG_CODE_PREFIX}{200 + i+1:03d}"
    for i in range(REGULAR_SETS):
        set_codes[f"OP{i+1:02d}"] = f"{OPTCG_CODE_PREFIX}{100 + i+1:03d}"
    for i in range(STARTER_DECKS):
        set_codes[f"ST{i+1:02d}"] = f"{OPTCG_CODE_PREFIX}{000 + i+1:03d}"
    set_codes["PROMO"] = f"{OPTCG_CODE_PREFIX}901"
    set_codes["OTHER"] = f"{OPTCG_CODE_PREFIX}801"
    return set_codes

if __name__ == "__main__":
    set_codes = build_card_set_codes()
    for set_name, set_code in set_codes.items():
        print(f"Fetching cards for set: {set_name} (code: {set_code})")
        response = requests.get(OPTCG_BASE_URL + set_code)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            f = open(f"{set_name}.html", "w", encoding="utf-8")
            f.write(soup.prettify())
            f.close()
            print(f"Saved HTML for set: {set_name}")
        else:
            print(f"Failed to fetch cards for set: {set_name} (status code: {response.status_code})")
        time.sleep(5)  # Sleep to avoid overwhelming the server
'''
- List of cards is loaded on page load, then each option and image is dynamically loaded when the user changes page
- All card info on page is loaded in the HTML when the page is loaded
- Just need to get the 6 digit code that corresponds to the page, then collect all the info for that page
- All images end in 260305, so we can use that to find the image URL
    - format: en.onepiece-cardgame.com/images/cardlist/card/[card code].png?260305

- Prefix: 569
- Premium Booster: 300
- Extra Booster: 200
- Regular Set: 100
- Starter Deck: 000
- Promo: 901
- Other: 801
    
- Get all optcg set codes from the selection menu
- Query the page for each set code, then get all the card info for that set in HTML
- Create a way to parse the HTML for each card, then save the info in a structured format (e.g., JSON, CSV)

- Wow each card sample image file path is also in the HTML
'''