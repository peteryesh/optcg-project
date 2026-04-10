from bs4 import BeautifulSoup
import json

def get_html_object_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup

def get_cards_from_html(soup):
    cards = {}
    tags = soup.find_all("dl", class_= "modalCol")
    for tag in tags:
        card = {}
        info_block = tag.find("div", class_="infoCol")
        card_code = info_block.span.text.strip()

        if card_code in cards:
            card["alt"] = tag["id"]
            card["set"] = format_card_data(tag.find("div", class_="getInfo").h3.next_sibling)
            card["img_path"] = tag.find("div", class_="frontCol").img["data-src"]
            cards[card_code]["alts"].append(card)
            continue

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
        card["set"] = format_card_data(tag.find("div", class_="getInfo").h3.next_sibling)
        if tag.find("div", class_="remarks"):
            card["notes"] = format_card_data(tag.find("div", class_="remarks").h3.next_sibling.text)
        card["img_path"] = tag.find("div", class_="frontCol").img["data-src"]
        card["alts"] = []
        cards[card["code"]] = card
    
    return cards

def format_card_data(str):
    
    return str.replace("\n", "").strip()

if __name__ == "__main__":
    soup = get_html_object_from_file("optcg_html/OP02.html")
    cards = get_cards_from_html(soup)
    with open("./optcg_json/OP02.json", "w", encoding="utf-8") as f:
        json.dump(cards, f)