import random
from logic_game import CellState

class SmartAI:
    def __init__(self, rows=10, cols=10, fleet_config=None):
        self.rows = rows
        self.cols = cols
        self.mode = "hunt"   # "hunt" hoặc "target"
        self.last_hits = []  # lưu các ô đang trúng chưa chìm
        self.fleet_config = fleet_config or []
    
    def choose_move(self, tracking_board, remaining_ships):
        """
        tracking_board: Board mà AI theo dõi Player (AI không thấy tàu, chỉ biết Hit/Miss).
        remaining_ships: danh sách tàu Player chưa chìm.
        """
        if self.mode == "target" and self.last_hits:
            move = self._target_mode(tracking_board)
            if move: 
                return move

        # Nếu không có target khả dụng → quay về hunt mode
        self.mode = "hunt"
        return self._hunt_mode(tracking_board, remaining_ships)

    def feedback(self, move, result, sunk_ship_len=None):
        """AI nhận phản hồi từ nước bắn"""
        r, c = move
        if result == "Hit":
            self.last_hits.append((r, c))
            self.mode = "target"
        elif result == "Sunk":
            self.last_hits.clear()
            self.mode = "hunt"
        # Miss thì không cần xử lý đặc biệt

    # =========================
    # HUNT MODE (probability map)
    # =========================
    def _hunt_mode(self, tracking_board, remaining_ships):
        scores = [[0]*self.cols for _ in range(self.rows)]
        ship_lengths = [s.size for s in remaining_ships if not s.is_sunk]

        for length in ship_lengths:
            for r in range(self.rows):
                for c in range(self.cols):
                    # --- check ngang ---
                    if c + length <= self.cols:
                        segment = [tracking_board.grid[r][c+i] for i in range(length)]
                        if all(cell in [CellState.EMPTY] for cell in segment):
                            for i in range(length):
                                scores[r][c+i] += 1
                    # --- check dọc ---
                    if r + length <= self.rows:
                        segment = [tracking_board.grid[r+i][c] for i in range(length)]
                        if all(cell in [CellState.EMPTY] for cell in segment):
                            for i in range(length):
                                scores[r+i][c] += 1

        # tìm max
        max_score = max(max(row) for row in scores)
        candidates = [(r, c) for r in range(self.rows) for c in range(self.cols)
                      if scores[r][c] == max_score]
        return random.choice(candidates) if candidates else None

    # =========================
    # TARGET MODE
    # =========================
    def _target_mode(self, tracking_board):
        # Lấy ô hit đầu tiên
        base_r, base_c = self.last_hits[0]
        directions = [(0,1),(0,-1),(1,0),(-1,0)]

        for dr, dc in directions:
            r, c = base_r + dr, base_c + dc
            if 0 <= r < self.rows and 0 <= c < self.cols:
                if tracking_board.grid[r][c] == CellState.EMPTY:
                    return (r, c)
        return None
