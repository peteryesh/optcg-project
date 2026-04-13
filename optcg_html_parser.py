from bs4 import BeautifulSoup
import json

main_sets = [
    "OP01",
    "OP02",
    "OP03",
    "OP04",
    "OP05",
    "OP06",
    "OP07",
    "OP08",
    "OP09",
    "OP10",
    "OP11",
    "OP12",
    "OP13",
    "OP14",
    "OP15",
]

extra_boosters = [
    "EB01",
    "EB02",
    "EB03",
]

prb_sets = [
    "PRB01",
    "PRB02",
]

starter_decks = [
    "ST01",
    "ST02",
    "ST03",
    "ST04",
    "ST05",
    "ST06",
    "ST07",
    "ST08",
    "ST09",
    "ST10",
    "ST11",
    "ST12",
    "ST13",
    "ST14",
    "ST15",
    "ST16",
    "ST17",
    "ST18",
    "ST19",
    "ST20",
    "ST21",
    "ST22",
    "ST23",
    "ST24",
    "ST25",
    "ST26",
    "ST27",
    "ST28",
    "ST29",
]

other = [
    "PROMO",
    "OTHER"
]

def all_sets():
    return main_sets + extra_boosters + prb_sets + starter_decks + other

def get_html_object_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup

def update_cards_from_html(cards, set, soup):
    tags = soup.find_all("dl", class_= "modalCol")
    for tag in tags:
        try:
            card = {}
            info_block = tag.find("div", class_="infoCol")
            card_code = info_block.span.text.strip()

            '''
            if the tag id contains an underscore, it is an alternate art card
            if the base card code does not exist, create the card and add it to the dictionary with the alternate art info, then when we process the base card, we will add the base card info to the existing card entry
            else, add the alt card info to the alts
            '''

            # Check if this is an alternate art card by looking for an underscore in the card code
            # If the card already exists in the cards dictionary, add this card as an alternate art to the existing card
            if "_" in tag["id"]:
                # print(f"Found alternate art for card code {card_code} in set {set}")
                if card_code not in cards:
                    cards[card_code] = {
                        "code": card_code,
                        "alts": [
                            {
                                "alt_code": tag["id"],
                                "set": format_card_data(tag.find("div", class_="getInfo").h3.next_sibling),
                                "img_path": tag.find("div", class_="frontCol").img["data-src"],
                                "artist": ""
                            }
                        ]
                    }
                else:
                    cards[card_code]["alts"].append({
                        "alt_code": tag["id"],
                        "set": format_card_data(tag.find("div", class_="getInfo").h3.next_sibling),
                        "img_path": tag.find("div", class_="frontCol").img["data-src"],
                        "artist": ""
                    })
                continue

            # print(f"Processing card code {card_code} in set {set}")
            card["code"] = card_code
            card["rarity"] = format_card_data(info_block.find_all("span")[1].text)
            card["class"] = format_card_data(info_block.find_all("span")[2].text)
            card["name"] = format_card_data(tag.find("div", class_="cardName").text)
            card["cost"] = format_card_data(tag.find("div", class_="cost").h3.next_sibling)
            card["attribute"] = format_card_data(tag.find("div", class_="attribute").i.text).split('/')
            card["power"] = format_card_data(tag.find("div", class_="power").h3.next_sibling)
            card["counter"] = format_card_data(tag.find("div", class_="counter").h3.next_sibling)
            card["color"] = format_card_data(tag.find("div", class_="color").h3.next_sibling).split('/')
            card["block"] = format_card_data(tag.find("div", class_="block").h3.next_sibling)
            card["card_type"] = format_card_data(tag.find("div", class_="feature").h3.next_sibling).split('/')
            card["effect"] = format_card_data(tag.find("div", class_="text").h3.next_sibling)

            additional_effects = tag.find("div", class_="text").find_all("br")
            if additional_effects:
                for effect in additional_effects:
                    if effect.next_sibling and effect.next_sibling.string and effect.next_sibling.string.strip():
                        card["effect"] += " " + format_card_data(effect.next_sibling.string.strip())

            card["set"] = format_card_data(tag.find("div", class_="getInfo").h3.next_sibling)
            if tag.find("div", class_="remarks"):
                card["notes"] = format_card_data(tag.find("div", class_="remarks").h3.next_sibling.text)
            card["img_path"] = tag.find("div", class_="frontCol").img["data-src"]
            card["artist"] = ""

            if card_code in cards:
                # If the card already exists, we have seen the alternate art before the base card, so we need to add the base card info to the existing card entry
                card["alts"] = cards[card_code]["alts"]
                cards[card_code] = card
            else:
                card["alts"] = []
                cards[card_code] = card

        except Exception as e:
            print(f"Error processing card from set {set} with tag id {tag['id']}: {e}")
    
    return cards

def generate_cardlist(card_sets):
    cards = {}
    for set in card_sets:
        soup = get_html_object_from_file(f"optcg_html/{set}.html")
        update_cards_from_html(cards, set, soup)
    return cards
    
# FUTURE: make an update json function that takes in the existing json file and updates it with any new cards or changes to existing cards, then saves the updated json file, this way we can easily keep our card data up to date without having to reprocess all the HTML files every time

def format_card_data(str):
    return str.replace("\n", "").strip()

if __name__ == "__main__":
    cards = generate_cardlist(all_sets())
    with open(f"./optcg_info.json", "w", encoding="utf-8") as f:
        json.dump(cards, f)