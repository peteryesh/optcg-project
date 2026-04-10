class Card:
    def __init__(self, code, block, name, color, card_class, rarity, card_type, effect = "", cost = None, power = None, counter = None, attribute = None, life = None, notes = ""):
        self.code = code
        self.block = block
        self.name = name
        self.color = color
        self.card_class = card_class
        self.rarity = rarity
        self.card_type = card_type
        self.effect = effect
        self.cost = cost
        self.power = power
        self.counter = counter
        self.attribute = attribute
        self.life = life
        self.notes = notes