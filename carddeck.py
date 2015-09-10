__author__ = 'Yeehawk'

import random

from kivy.uix.image import Image


class Deck:
    def __init__(self):

        one_suit_name = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "j", "q", "k", "a"]
        one_suit_val = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11]

        self.cards = []

        # use for loop to populate deck... don't simply use one_deck * 6,
        # because objects will be duplicated, and will get trouble later when add card pic.

        for i in range(6):
            for s in ["club", "diamond", "heart", "spade"]:
                for name, value in zip(one_suit_name, one_suit_val):
                    card = Card(name, value, s)
                    self.cards.append(card)

        random.shuffle(self.cards)
        self.card_counter = 0
        # self.parent.status.text= "--------------deck shuffled, counter reset -------------------"

    def draw(self):

        card = self.cards.pop()
        if card.value <= 6:
            self.card_counter += 1
        elif card.value >= 10:
            self.card_counter -= 1
        return card


class Card:
    def __init__(self, name, value, suit):
        self.name = name
        self.value = value
        self.suit = suit
        self.card_label = CardLabel()

    def display(self, hand, hidden=False):

        self.card_label.pos_hint = {'center_x': 0.2 + 0.1 * len(hand.cards), 'center_y': hand.pos_y()}

        if hidden is True:
            fn = "back"
        else:
            fn = self.suit[0] + self.name

        self.card_label.source = "pic\\%s.png" % fn
        game_window.game_table.add_widget(self.card_label)

    def no_display(self):
        game_window.game_table.remove_widget(self.card_label)


class CardLabel(Image):
    pass
