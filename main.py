__author__ = 'Yeehawk'

from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.properties import ListProperty

import handsplayer
import carddeck


class Table(RelativeLayout):
    pass


class PlayerChoices(BoxLayout):
    pass


class BetWindow(BoxLayout):
    pass


class ScrollStatus(ScrollView):
    pass


class HintLabel(Label):
    # not in init! it is a class var!
    hint_color = ListProperty()
    pass


class GameWindow(BoxLayout):
    def __init__(self):
        super().__init__()
        player_name = 'Andy'

        self.player = handsplayer.Player(player_name)
        self.deck = carddeck.Deck()

        self.dealer = handsplayer.Dealer()
        self.player_strategy = handsplayer.PlayerStrategy()

        self.current_hand = None
        self.player_choices = PlayerChoices()
        self.current_hand_indicator = Image(source="pic\\current_hand.png")

    def deal(self):

        for hand in self.player.hands:
            hand.hit()
            hand.hit()
        self.dealer.hand.hit()
        # hide 2nd dealer card
        self.dealer.hand.hit(True)

    def insurance(self):
        pass

    def active_hand_gen(self):
        # use generator instead of loop..
        # because user interaction expected for each hand.....need to break code...
        for hand in self.player.hands:
            if hand.clear is False:
                yield hand

    def next_hand(self):
        try:
            hand = next(self.active_hands)
            return hand
        except StopIteration:
            self.status.text = self.status.text + "no more active hand, ,pls start a new game\n"
            return None

    def clean_table(self):
        self.game_table.clear_widgets()

    def update_buttons(self):
        for button in self.player_choices.children:
            button.disabled = True
        if self.current_hand is not None:
            if self.current_hand.count() <= 21:
                self.player_choices.ids.stand_btn.disabled = False
                self.player_choices.ids.hit_btn.disabled = False
                if len(self.current_hand.cards) == 2:
                    self.player_choices.ids.double_btn.disabled = False
                    self.player_choices.ids.surrender_btn.disabled = False
                    if self.current_hand.cards[0].value == self.current_hand.cards[1].value:
                        self.player_choices.ids.split_btn.disabled = False

        else:
            return

    def update_current_hand_indicator(self):

        self.game_table.remove_widget(self.current_hand_indicator)

        self.current_hand_indicator.pos_hint = {'center_x': 0.1, 'center_y': self.current_hand.pos_y()}
        self.current_hand_indicator.size_hint = (0.15, 0.15)

        self.game_table.add_widget(self.current_hand_indicator)

    def start_game(self):

        self.clean_table()
        self.cleanup_hands()
        self.ids.play_btn.disabled = True

        # shuffle deck if necessary
        if len(self.deck.cards) < 50:
            self.deck.__init__()

        if not self.player.hands:
            self.player.hands.append(handsplayer.PlayerHand(self.player))

            # add more hands if want to play multiple hands
            self.player.hands.append(handsplayer.PlayerHand(self.player))

        self.game_table.add_widget(BetWindow())

    def bet(self, amount, bet_window):
        self.game_table.remove_widget(bet_window)

        for hand in self.player.hands:
            hand.bet = amount
            self.player.money -= hand.bet
            self.player.bet_total += hand.bet

        self.after_bet()

    def after_bet(self):
        # start to deal
        self.deal()

        # insurance if dealer first card is Ace
        self.insurance()


        # dealer holing
        if self.dealer.hand.count() == 21:

            # dealer BJ
            self.dealer.hand.show_point("BlackJack")

            for hand in self.player.hands:
                hand.count()
                if hand.point == 21:
                    hand.show_point("BlackJack")
                    hand.push()
                else:
                    hand.show_point(str(hand.point))
                    hand.lose()

        else:
            # nobody home...
            # check if player blackjack
            for hand in self.player.hands:
                hand.count()
                hand.show_point(str(hand.point))
                if hand.count() == 21:
                    hand.point_icon.text = "BlackJack"
                    hand.win(blackjack=True)

        self.active_hands = self.active_hand_gen()
        self.current_hand = self.next_hand()

        if self.current_hand is None:
            # no active hands.. end...
            # uncover dealer hidden card
            self.dealer.hand.cards[1].no_display()
            self.dealer.hand.cards[1].display(self.dealer.hand)
            self.ids.play_btn.disabled = False
        else:
            # continue on first active hand
            self.update_current_hand_indicator()
            # add buttons dynamically
            self.game_table.add_widget(self.player_choices)
            self.update_buttons()

    def player_move(self, choice):

        hint = self.current_hand.hint()
        if choice == hint:
            # self.status.text = self.status.text + "right decision\n"
            self.show_hint()
        else:
            # self.status.text = self.status.text + "%s might be better choice\n " % hint
            self.show_hint(hint)

        if choice == "H":
            self.current_hand.hit()
        elif choice == "S":
            self.current_hand.stand()
        elif choice == "SP":
            self.current_hand.split()
        elif choice == "SU":
            self.current_hand.surrender()
        elif choice == "D":
            self.current_hand.double()

        self.current_hand.count()
        if self.current_hand.point > 21:
            self.current_hand.point_icon.text = str(self.current_hand.point) + " Busted!"
            self.current_hand.lose()
        else:
            self.current_hand.point_icon.text = str(self.current_hand.point)
            if self.current_hand.point == 21:
                self.current_hand.stand()

        if not self.current_hand.stop:
            # provide applicable actions for current hand
            self.update_buttons()

        else:

            # find next active hand which is not 21 and not stopped

            self.current_hand = self.next_hand()
            # next line two conditions can  not switch order
            while self.current_hand and (self.current_hand.count() == 21 or self.current_hand.stop):
                self.current_hand.stand()
                self.current_hand = self.next_hand()

            # if can not find ... means no player actions needed..
            if not self.current_hand:
                self.game_table.remove_widget(self.current_hand_indicator)
                self.complete_game()
            else:
                self.update_current_hand_indicator()
                self.update_buttons()

    def complete_game(self):

        # uncover dealer hidden card
        self.dealer.hand.cards[1].no_display()
        self.dealer.hand.cards[1].display(self.dealer.hand)
        self.dealer.hand.show_point(str(self.dealer.hand.point))

        # if there are hands not cleared:
        # dealer draw to 17 or above
        still_live_hands = []

        for hand in self.player.hands:
            if hand.clear is False:
                still_live_hands.append(hand)

        if still_live_hands:
            self.dealer.follow_rule()

            dealer_point = self.dealer.hand.count()

            # if dealer busted, all active hands win
            if dealer_point > 21:
                for hand in still_live_hands:
                    hand.win()

            # compare points
            else:
                for hand in still_live_hands:

                    player_point = hand.count()
                    if player_point > dealer_point:
                        hand.win()
                    elif player_point == dealer_point:
                        hand.push()
                    else:
                        hand.lose()

        self.cleanup_hands()
        self.game_table.remove_widget(self.player_choices)
        self.ids.play_btn.disabled = False

    def cleanup_hands(self):

        # clean up all hands
        self.dealer.hand.cards = []
        self.player.hands = []

        # disable all player action buttons
        for button in self.player_choices.children:
            button.disabled = True

    def stat(self):
        # print(player.money_history)
        if self.player.bet_total != 0:
            ratio = (10000 - self.player.money) / self.player.bet_total
            self.status.text += "player %s performance:  \n" % self.player.name + \
                                str(self.player.win_push_lose) + "   loss = " + str(10000 - self.player.money) + \
                                "   loss:total_bet= " + str(ratio) + "\n" + "player money: %d\n" % self.player.money

    def show_hint(self, better=None):
        # show hint, and remove after 1s
        hint_label = HintLabel()
        if better:
            hint_label.text = "%s might be better." % better

            # hint_color is a list property. hint_label canvas will change color depending on this property change..
            hint_label.hint_color = 0.75, 0.85, 0.1, 1
            game_window.game_table.add_widget(hint_label)
        else:
            hint_label.text = "Good Choice!"
            hint_label.hint_color = 0., 0.85, 0.5, 1  # use greenish color for correct choice..
            game_window.game_table.add_widget(hint_label)

        # use Clock to wait... kivy does not like sleep
        Clock.schedule_once(self.remove_hint(hint_label), 1)

    def remove_hint(self, hint_label):
        # this is a function closure to wrap remove_widget...
        # it returns a func that does not accept parameters, as required in Clock call-back
        def rr(self):
            game_window.game_table.remove_widget(hint_label)

        return rr


class BlackjackApp(App):
    def build(self):
        global game_window
        game_window = GameWindow()
        handsplayer.game_window = game_window
        carddeck.game_window = game_window
        return game_window


if __name__ == "__main__":
    BlackjackApp().run()
