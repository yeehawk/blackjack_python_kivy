__author__ = 'Yeehawk'

from kivy.uix.label import Label


class Hand:
    def __init__(self, owner):
        self.cards = []
        self.owner = owner
        self.stop = False
        self.soft = False
        self.point = 0
        self.point_icon = HandPoint()

    def count(self):
        # only one ace can be counted as 11
        self.point = 0
        self.soft = False
        has_ace = False
        for card in self.cards:
            if card.value == 11:
                self.point += 1
                has_ace = True
            else:
                self.point += card.value
        if has_ace and self.point <= 11:
            self.point += 10
            self.soft = True
        return self.point

    def hit(self, dealer_hidden=False):
        new_card = game_window.deck.draw()
        self.cards.append(new_card)
        new_card.display(self, dealer_hidden)

    def stand(self):
        self.stop = True

    def show_point(self, point):
        # only show/add, not update/remove... maybe refactored later?
        self.point_icon.text = point
        self.point_icon.pos_hint = {'center_x': 0.9, 'center_y': self.pos_y()}
        game_window.game_table.add_widget(self.point_icon)

    def pos_y(self):
        if self.owner.name == "dealer":
            y = 0.85
        else:
            y = 0.6 - 0.22 * self.owner.hands.index(self)
        return y


class Player:
    def __init__(self, player_name):
        self.name = player_name
        self.money = 10000
        self.hands = []
        self.bet_total = 0
        self.win_push_lose = [0, 0, 0]
        # self.money_history = []
        self.hands.append(PlayerHand(self))


class PlayerHand(Hand):
    def __init__(self, owner):
        Hand.__init__(self, owner)
        self.bet = 0
        self.insured = False
        self.clear = False

    def hint(self):
        column_index = game_window.dealer.hand.cards[0].value - 2
        if len(self.cards) == 2 and self.cards[0].value == self.cards[1].value:
            row_index = self.cards[0].value - 2
            code = game_window.player_strategy.pair[row_index][column_index]
        else:
            points = self.count()
            if self.soft is True:
                row_index = points - 13
                code = game_window.player_strategy.soft[row_index][column_index]
            else:
                if points <= 8:
                    row_index = 0
                elif points >= 17:
                    row_index = 9
                else:
                    row_index = points - 8
                code = game_window.player_strategy.normal[row_index][column_index]

        if code == "SU" and len(self.cards) != 2:
            code = "H"

        elif code == "Dh":
            if len(self.cards) == 2:
                code = "D"
            else:
                code = "H"
        elif code == "Ds":
            if len(self.cards) == 2:
                code = "D"
            else:
                code = "S"
        elif code not in ["H", "S", "SP", "SU"]:
            raise Exception

        return code

    def surrender(self):

        self.owner.money += self.bet / 2

        self.stop = True
        self.owner.win_push_lose[2] += 1
        # self.owner.money_history.append(self.owner.money)
        self.clear = True

        hand_result = HandResult()
        hand_result.text = "Lose:%d" % (self.bet / 2)
        hand_result.pos_hint = {'center_x': 0.1, 'center_y': self.pos_y()}
        game_window.game_table.add_widget(hand_result)

        self.bet = 0

    def double(self):

        self.owner.money -= self.bet
        self.bet *= 2
        self.hit()
        self.stop = True

    def split(self):

        newhand = PlayerHand(self.owner)
        card = self.cards.pop()
        card.no_display()

        newhand.cards.append(card)
        self.owner.money -= self.bet
        newhand.bet = self.bet

        if self.cards[0].value == 11:
            self.stop = True
            newhand.stop = True

        self.owner.hands.append(newhand)
        self.hit()

        # hit after append to hands, to make sure card can display itself with correct hand parameter
        card.display(self.owner.hands[-1])
        self.owner.hands[-1].hit()
        self.owner.hands[-1].count()
        self.owner.hands[-1].show_point(str(self.owner.hands[-1].point))

    def win(self, blackjack=False):
        if blackjack is True:
            win_amount = self.bet * 1.5


        else:
            win_amount = self.bet

        self.owner.money += (win_amount + self.bet)

        self.bet = 0
        # self.owner.money_history.append(self.owner.money)
        self.clear = True
        self.stop = True
        self.owner.win_push_lose[0] += 1

        hand_result = HandResult()
        hand_result.text = "Win:%d" % win_amount
        hand_result.pos_hint = {'center_x': 0.1, 'center_y': self.pos_y()}
        game_window.game_table.add_widget(hand_result)

    def lose(self):

        # self.owner.money_history.append(self.owner.money)
        self.clear = True
        self.stop = True
        self.owner.win_push_lose[2] += 1

        hand_result = HandResult()
        hand_result.text = "Lose:%d" % self.bet
        hand_result.pos_hint = {'center_x': 0.1, 'center_y': self.pos_y()}
        game_window.game_table.add_widget(hand_result)

        self.bet = 0

    def push(self):
        self.owner.money += self.bet
        self.bet = 0
        # self.owner.money_history.append(self.owner.money)
        self.clear = True
        self.stop = True
        self.owner.win_push_lose[1] += 1

        hand_result = HandResult()
        hand_result.text = "Push"
        hand_result.pos_hint = {'center_x': 0.1, 'center_y': self.pos_y()}
        game_window.game_table.add_widget(hand_result)


class Dealer:
    def __init__(self):
        self.name = 'dealer'
        self.hand = Hand(self)

    def follow_rule(self):
        while self.hand.count() < 17:
            self.hand.hit()
            self.hand.count()
        self.hand.point_icon.text = str(self.hand.point)


class PlayerStrategy:
    pair = [
        ["SP", "SP", "SP", "SP", "SP", "SP", "H", "H", "H", "H"],
        ["SP", "SP", "SP", "SP", "SP", "SP", "H", "H", "H", "H"],
        ["H", "H", "H", "SP", "SP", "H", "H", "H", "H", "H"],
        ["Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "H", "H"],
        ["SP", "SP", "SP", "SP", "SP", "H", "H", "H", "H", "H"],
        ["SP", "SP", "SP", "SP", "SP", "SP", "H", "H", "H", "H"],
        ["SP", "SP", "SP", "SP", "SP", "SP", "SP", "SP", "SP", "SP"],
        ["SP", "SP", "SP", "SP", "SP", "S", "SP", "SP", "S", "S"],
        ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
        ["SP", "SP", "SP", "SP", "SP", "SP", "SP", "SP", "SP", "SP"]
    ]

    soft = [
        ["H", "H", "H", "Dh", "Dh", "H", "H", "H", "H", "H"],
        ["H", "H", "H", "Dh", "Dh", "H", "H", "H", "H", "H"],
        ["H", "H", "Dh", "Dh", "Dh", "H", "H", "H", "H", "H"],
        ["H", "H", "Dh", "Dh", "Dh", "H", "H", "H", "H", "H"],
        ["H", "Dh", "Dh", "Dh", "Dh", "H", "H", "H", "H", "H"],
        ["S", "Ds", "Ds", "Ds", "Ds", "S", "S", "H", "H", "H"],
        ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
        ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"],
        ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"]
    ]

    normal = [
        ["H", "H", "H", "H", "H", "H", "H", "H", "H", "H"],
        ["H", "Dh", "Dh", "Dh", "Dh", "H", "H", "H", "H", "H"],
        ["Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "H", "H"],
        ["Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "Dh", "H"],
        ["H", "H", "S", "S", "S", "H", "H", "H", "H", "H"],
        ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
        ["S", "S", "S", "S", "S", "H", "H", "H", "H", "H"],
        ["S", "S", "S", "S", "S", "H", "H", "H", "SU", "H"],
        ["S", "S", "S", "S", "S", "H", "H", "SU", "SU", "SU"],
        ["S", "S", "S", "S", "S", "S", "S", "S", "S", "S"]
    ]


class HandPoint(Label):
    pass


class HandResult(Label):
    pass
