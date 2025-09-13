# FILE: ai_hybrid.py
# AI kết hợp Blind Search + Heuristic Search + Adversarial Search

import random
from ai_blind import BlindAI
from ai_heuristic import HeuristicAI

class HybridAI:
    def __init__(self, board_size=10, ships=[5,4,3,3,2]):
        self.board_size = board_size
        self.remaining_ships = ships[:]

        # Các module chiến lược
        self.blind = BlindAI(board_size)
        self.heuristic = HeuristicAI(board_size, ships)
        # Adversarial tích hợp trực tiếp trong Hybrid
        self.shots_taken = set()
        self.hits = set()
        self.misses = set()

        # Trạng thái
        self.mode = "blind"
        self.turn_count = 0

    def estimate_player_strategy(self, r, c):
        """
        Rule-based player model:
        - Ưu tiên trung tâm hơn góc/biên
        - Giả định người chơi có xu hướng giấu tàu ở biên
        """
        center_dist = abs(r - self.board_size/2) + abs(c - self.board_size/2)
        max_dist = self.board_size
        return center_dist / max_dist   # 0 = trung tâm, 1 = xa (biên)

    def adversarial_search(self):
        """Adversarial search: Heuristic + Player Model"""
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
        return move

    def choose_move(self):
        """Chọn nước đi tiếp theo dựa vào mode"""
        self.turn_count += 1

        if self.mode == "blind":
            move = self.blind.choose_move()

        elif self.mode == "heuristic":
            move = self.heuristic.choose_move()

        else:  # adversarial
            move = self.adversarial_search()

        self.shots_taken.add(move)
        return move

    def feedback(self, move, result, sunk_ship_len=None):
        """
        Nhận phản hồi từ game
        - result: "Hit", "Miss", "Sunk"
        - sunk_ship_len: độ dài tàu bị chìm (nếu có)
        """
        r, c = move
        res = result.lower()

        # cập nhật heuristic
        self.heuristic.feedback(move, res, sunk_ship_len)

        if result == "Hit":
            self.hits.add(move)
            self.mode = "heuristic"  # chuyển sang heuristic nếu trúng

        elif result == "Sunk":
            if sunk_ship_len and sunk_ship_len in self.remaining_ships:
                self.remaining_ships.remove(sunk_ship_len)
            # Nếu hết hit đang “treo” → quay lại blind
            if not self.heuristic.hits:
                self.mode = "blind"

        elif result == "Miss":
            self.misses.add(move)

        # 🔹 Quy tắc nâng cấp sang adversarial
        if self.turn_count > 20 and len(self.remaining_ships) > 0:
            # khi trận kéo dài hoặc còn tàu lớn chưa tìm thấy
            if max(self.remaining_ships) >= 4:  
                self.mode = "adversarial"
