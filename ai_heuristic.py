# FILE: ai_heuristic.py
# Heuristic AI cho Battleship: Probability Grid + Target Mode

import random
from logic_game import CellState

class HeuristicAI:
    def __init__(self, board_size=10, ships=[5,4,3,3,2]):
        self.board_size = board_size
        self.remaining_ships = ships[:]
        self.hits = []       # các ô đã trúng nhưng chưa chìm tàu
        self.shots_taken = set()

    # -------------------------------
    # Heatmap dựa trên tàu còn lại
    # -------------------------------
    def compute_probability_grid(self, tracking_board, remaining_ships):
        rows, cols = tracking_board.rows, tracking_board.cols
        scores = [[0]*cols for _ in range(rows)]
        ship_lengths = [s.size for s in remaining_ships if not s.is_sunk]

        for length in ship_lengths:
            # duyệt tất cả vị trí khả thi
            for r in range(rows):
                for c in range(cols):
                    # check ngang
                    if c + length <= cols:
                        segment = [tracking_board.grid[r][c+i] for i in range(length)]
                        if all(cell in [CellState.EMPTY] for cell in segment):
                            for i in range(length):
                                scores[r][c+i] += 1

                    # check dọc
                    if r + length <= rows:
                        segment = [tracking_board.grid[r+i][c] for i in range(length)]
                        if all(cell in [CellState.EMPTY] for cell in segment):
                            for i in range(length):
                                scores[r+i][c] += 1
        return scores

    # -------------------------------
    # Chọn ô tiếp theo
    # -------------------------------
    def choose_move(self, tracking_board, remaining_ships):
        # Nếu đang có hits → Target Mode
        if self.hits:
            r, c = self.hits[-1]
            neighbors = [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]
            neighbors = [(r,c) for r,c in neighbors
                         if 0 <= r < self.board_size and 0 <= c < self.board_size
                         and (r,c) not in self.shots_taken]
            if neighbors:
                return random.choice(neighbors)

        # Nếu không có hit → Hunt Mode
        scores = self.compute_probability_grid(tracking_board, remaining_ships)
        max_score = max(max(row) for row in scores)
        candidates = [(r,c) for r in range(self.board_size) for c in range(self.board_size)
                      if scores[r][c] == max_score and (r,c) not in self.shots_taken]

        return random.choice(candidates) if candidates else None

    # -------------------------------
    # Nhận phản hồi từ game
    # -------------------------------
    def feedback(self, move, result, sunk_ship_len=None):
        r, c = move
        self.shots_taken.add(move)

        if result.lower() == "hit":
            self.hits.append(move)

        elif result.lower() == "sunk":
            if sunk_ship_len and sunk_ship_len in self.remaining_ships:
                self.remaining_ships.remove(sunk_ship_len)
            # reset hits vì tàu đó đã chìm
            self.hits = [h for h in self.hits if h != move]

        elif result.lower() == "miss":
            pass  # không cần lưu gì thêm
