# # FILE: ai_heuristic.py
# # Heuristic AI với Hunt & Target cho Battleship

# import random

# class HeuristicAI:
#     def __init__(self, board_size=10, ships=[5,4,3,3,2]):
#         self.board_size = board_size
#         self.shots_taken = set()
#         self.hits = set()   # các ô đã trúng nhưng chưa giải quyết xong (chưa chìm tàu)
#         self.misses = set()
#         self.remaining_ships = ships[:]  # danh sách độ dài tàu còn lại

#     # ----------------------------------------------------------------------
#     # Kiểm tra đặt giả định tàu hợp lệ
#     def valid_ship_placement(self, r, c, length, direction):
#         cells = []
#         if direction == "H":
#             if c + length > self.board_size:
#                 return None
#             cells = [(r, c+i) for i in range(length)]
#         else:
#             if r + length > self.board_size:
#                 return None
#             cells = [(r+i, c) for i in range(length)]
        
#         # Nếu bất kỳ ô nào nằm trong misses thì loại bỏ
#         for cell in cells:
#             if cell in self.misses:
#                 return None
#         return cells

#     # ----------------------------------------------------------------------
#     # Tính xác suất cho toàn bộ ô
#     def compute_probability_grid(self):
#         prob_grid = [[0]*self.board_size for _ in range(self.board_size)]

#         for ship_len in self.remaining_ships:
#             for r in range(self.board_size):
#                 for c in range(self.board_size):
#                     # horizontal
#                     cells = self.valid_ship_placement(r, c, ship_len, "H")
#                     if cells:
#                         for cell in cells:
#                             if cell not in self.shots_taken:
#                                 prob_grid[cell[0]][cell[1]] += 1
#                     # vertical
#                     cells = self.valid_ship_placement(r, c, ship_len, "V")
#                     if cells:
#                         for cell in cells:
#                             if cell not in self.shots_taken:
#                                 prob_grid[cell[0]][cell[1]] += 1
#         return prob_grid

#     # ----------------------------------------------------------------------
#     # Lấy nước đi
#     def choose_move(self):
#     # Nếu có hit → Target mode
#         if self.hits:
#             move = self.target_mode()
#             if move:
#                 self.shots_taken.add(move)
#                 return move
#             # ⚠ Nếu target_mode không tìm được neighbor, fallback về Hunt
#             else:
#                 self.hits.clear()   # reset, quay lại Hunt
        
#         # Hunt mode (tính xác suất)
#         prob_grid = self.compute_probability_grid()
#         max_val, candidates = -1, []
#         for r in range(self.board_size):
#             for c in range(self.board_size):
#                 if (r, c) not in self.shots_taken:
#                     if prob_grid[r][c] > max_val:
#                         max_val = prob_grid[r][c]
#                         candidates = [(r, c)]
#                     elif prob_grid[r][c] == max_val:
#                         candidates.append((r, c))
#         move = random.choice(candidates)
#         self.shots_taken.add(move)
#         return move


#     # ----------------------------------------------------------------------
#     # Target mode: ưu tiên bắn quanh các hit
#     def target_mode(self):
#         neighbors = []

#         # Nếu có >=2 hit → đoán theo hướng
#         hits_list = sorted(list(self.hits))
#         if len(hits_list) >= 2:
#             r1, c1 = hits_list[0]
#             r2, c2 = hits_list[1]
#             if r1 == r2:  # cùng hàng → tàu nằm ngang
#                 row = r1
#                 min_c, max_c = min(c1, c2), max(c1, c2)
#                 if min_c-1 >= 0 and (row, min_c-1) not in self.shots_taken:
#                     neighbors.append((row, min_c-1))
#                 if max_c+1 < self.board_size and (row, max_c+1) not in self.shots_taken:
#                     neighbors.append((row, max_c+1))
#             elif c1 == c2:  # cùng cột → tàu nằm dọc
#                 col = c1
#                 min_r, max_r = min(r1, r2), max(r1, r2)
#                 if min_r-1 >= 0 and (min_r-1, col) not in self.shots_taken:
#                     neighbors.append((min_r-1, col))
#                 if max_r+1 < self.board_size and (max_r+1, col) not in self.shots_taken:
#                     neighbors.append((max_r+1, col))
#         else:
#             # Nếu chỉ có 1 hit → thử 4 hướng
#             for (r, c) in self.hits:
#                 for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
#                     nr, nc = r+dr, c+dc
#                     if 0 <= nr < self.board_size and 0 <= nc < self.board_size:
#                         if (nr, nc) not in self.shots_taken:
#                             neighbors.append((nr, nc))

#         if neighbors:
#             return random.choice(neighbors)
#         return None

#     # ----------------------------------------------------------------------
#     # Cập nhật phản hồi
#     def feedback(self, move, result, sunk_ship_len=None):
#         if result.lower() == "hit":
#             self.hits.add(move)
#         elif result.lower() == "miss":
#             self.misses.add(move)
#         elif result.lower() == "sunk":
#             # Nếu biết độ dài tàu → loại khỏi remaining_ships
#             if sunk_ship_len and sunk_ship_len in self.remaining_ships:
#                 self.remaining_ships.remove(sunk_ship_len)
#             # reset hit vì tàu đã chìm
#             self.hits.clear()



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
