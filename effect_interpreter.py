import json

def parse_effect(effect):
    words = []
    i = 0
    word = ""
    grouped_text = False
    open_bracket = False
    while i < len(effect):
        if effect[i] in ["[", "<", "{", "("] and not open_bracket:
            grouped_text = True
            open_bracket = True
        elif effect[i] in ["]", ">", "}" , ")"] and open_bracket:
            grouped_text = False
            open_bracket = False
        elif effect[i] == "\"" and not open_bracket:
            grouped_text = not grouped_text

        if effect[i] == " " and not grouped_text:
            words.append(word)
            word = ""
        elif not effect[i] in [".", ",", ";", ":", "!", "?"]:
            word += effect[i].upper()
        
        if i == len(effect) - 1:
            words.append(word)

        i += 1

    return words

def get_effect_word_counts(effect):
    effect_words = parse_effect(effect)
    word_counts = {}
    for word in effect_words:
        if word in word_counts:
            word_counts[word] += 1
        else:
            word_counts[word] = 1
    return word_counts

if __name__ == "__main__":
    word_totals = {}
    with open("optcg_info.json", "r") as f:
        cards = json.load(f)
        for card_code in cards:
            effect = cards[card_code]["effect"]
            if effect != "-":
                word_counts = get_effect_word_counts(effect)
                for word, count in word_counts.items():
                    if word in word_totals:
                        word_totals[word] += count
                    else:
                        word_totals[word] = count
    with open("effect_word_counts.txt", "w") as f:
        for word, total in sorted(word_totals.items(), key=lambda item: item[1], reverse=False):
            f.write(f"{word}: {total}\n")