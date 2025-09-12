# FILE: ai_hybrid.py
# AI kết hợp Blind Search + Heuristic Search

import random
from ai_blind import BlindAI
from ai_heuristic import HeuristicAI

class HybridAI:
    def __init__(self, board_size=10, ships=[5, 4, 3, 3, 2]):
        self.board_size = board_size
        self.remaining_ships = ships[:]

        self.blind = BlindAI(board_size)
        self.heuristic = HeuristicAI(board_size, ships)
        self.mode = "blind"  # bắt đầu ở chế độ blind

    def choose_move(self):
        """Chọn nước đi tiếp theo"""
        if self.mode == "blind":
            move = self.blind.choose_move()
        else:
            move = self.heuristic.choose_move()
        return move

    def feedback(self, move, result, sunk_ship_len=None):
        """
        Nhận phản hồi từ game sau mỗi lần bắn
        - move: (row, col)
        - result: "Hit", "Miss", "Sunk"
        - sunk_ship_len: độ dài tàu bị chìm (nếu có)
        """
        r, c = move
        res = result.lower()

        # cập nhật heuristic với mọi kết quả
        self.heuristic.feedback(move, res, sunk_ship_len)

        if result == "Hit":
            # nếu bắn trúng thì chuyển sang heuristic mode
            self.mode = "heuristic"

        elif result == "Sunk":
            if sunk_ship_len and sunk_ship_len in self.remaining_ships:
                self.remaining_ships.remove(sunk_ship_len)

            # Nếu không còn ô "hit" chưa giải quyết → quay về blind
            if not self.heuristic.hits:
                self.mode = "blind"

        elif result == "Miss":
            # vẫn giữ nguyên mode, chỉ heuristic cập nhật
            pass
