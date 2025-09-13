import random
from ai_heuristic import HeuristicAI

class AdversarialAI:
    def __init__(self, board_size=10, ships=[5,4,3,3,2]):
        self.board_size = board_size
        self.remaining_ships = ships[:]
        self.heuristic = HeuristicAI(board_size, ships)
        self.shots_taken = set()

    def estimate_player_strategy(self, r, c):
        """Ước lượng người chơi giấu tàu ở biên nhiều hơn trung tâm"""
        center_dist = abs(r - self.board_size/2) + abs(c - self.board_size/2)
        max_dist = self.board_size
        return center_dist / max_dist   # 0 = trung tâm, 1 = biên

    def choose_move(self):
        prob_grid = self.heuristic.compute_probability_grid()
        best_score, best_moves = -1, []

        for r in range(self.board_size):
            for c in range(self.board_size):
                if (r, c) in self.shots_taken:
                    continue
                p_hit = prob_grid[r][c]
                p_hide = self.estimate_player_strategy(r, c)
                score = 0.7 * p_hit + 0.3 * (1 - p_hide)
                if score > best_score:
                    best_score, best_moves = score, [(r, c)]
                elif score == best_score:
                    best_moves.append((r, c))

        move = random.choice(best_moves)
        self.shots_taken.add(move)
        return move

    def feedback(self, move, result, sunk_ship_len=None):
        self.heuristic.feedback(move, result, sunk_ship_len)
        if result == "Sunk" and sunk_ship_len and sunk_ship_len in self.remaining_ships:
            self.remaining_ships.remove(sunk_ship_len)
