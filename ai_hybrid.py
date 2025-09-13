import random
from ai_blind import BlindAI
from ai_heuristic import HeuristicAI
from ai_adversarial import AdversarialAI

class HybridAI:
    def __init__(self, board_size=10, ships=[5,4,3,3,2]):
        self.blind = BlindAI(board_size)
        self.heuristic = HeuristicAI(board_size, ships)
        self.adversarial = AdversarialAI(board_size, ships)

        self.mode = "blind"
        self.turn_count = 0

    def choose_move(self):
        self.turn_count += 1

        if self.mode == "blind":
            move = self.blind.choose_move()
        elif self.mode == "heuristic":
            move = self.heuristic.choose_move()
        else:  # adversarial
            move = self.adversarial.choose_move()

        return move

    def feedback(self, move, result, sunk_ship_len=None):
        self.heuristic.feedback(move, result, sunk_ship_len)
        self.adversarial.feedback(move, result, sunk_ship_len)

        if result == "Hit":
            self.mode = "heuristic"
        elif result == "Sunk" and not self.heuristic.hits:
            self.mode = "blind"

        # sau nhiều lượt hoặc còn tàu lớn → chuyển sang adversarial
        if self.turn_count > 20 and self.adversarial.remaining_ships:
            if max(self.adversarial.remaining_ships) >= 4:
                self.mode = "adversarial"
