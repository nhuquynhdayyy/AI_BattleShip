# FILE: logic_game.py
# Battleship core logic with sink detection + remaining ships utility

import random
import re
import os

# ==============================================================================
# SECTION 1: CÁC CẤU TRÚC DỮ LIỆU CỐT LÕI
# ==============================================================================

class CellState:
    """Định nghĩa các trạng thái có thể có của một ô trên bản đồ."""
    EMPTY = 0
    SHIP = 1
    HIT = 2
    MISS = 3
    SUNK_SHIP = 4

FLEET_CONFIG = [
    {"name": "Carrier", "size": 5},
    {"name": "Battleship", "size": 4},
    {"name": "Cruiser", "size": 3},
    {"name": "Submarine", "size": 3},
    {"name": "Destroyer", "size": 2},
]

class Ship:
    """Đại diện cho một con tàu với các thuộc tính và trạng thái."""
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.hits_taken = 0
        self.is_sunk = False
        self.coordinates = []
        self.orientation = None
        self.start_pos = None

    def take_hit(self):
        """Ghi nhận một lượt bắn trúng và kiểm tra xem tàu đã chìm chưa."""
        self.hits_taken += 1
        if self.hits_taken >= self.size:
            self.is_sunk = True
            return True
        return False

class Board:
    """
    Quản lý bản đồ, logic đặt tàu, và xử lý các phát bắn.
    """
    def __init__(self, rows=10, cols=10):
        self.rows = rows
        self.cols = cols
        self.grid = [[CellState.EMPTY for _ in range(cols)] for _ in range(rows)]
        self.ships = []

    def _is_valid_placement(self, ship_size, start_row, start_col, orientation):
        """
        *** PHIÊN BẢN MỚI: CHỈ KIỂM TRA CHỒNG CHÉO, CHO PHÉP TÀU CHẠM NHAU ***
        Kiểm tra xem vị trí đặt tàu có hợp lệ không (trong biên, không chồng chéo).
        """
        # 1. Kiểm tra không nằm ngoài biên
        if orientation == "horizontal":
            if not (0 <= start_row < self.rows and 0 <= start_col < self.cols and start_col + ship_size <= self.cols):
                return False
        else:  # vertical
            if not (0 <= start_row < self.rows and 0 <= start_col < self.cols and start_row + ship_size <= self.rows):
                return False

        # 2. Lấy danh sách tọa độ tiềm năng
        potential_coords = []
        for i in range(ship_size):
            r = start_row + (i if orientation == "vertical" else 0)
            c = start_col + (i if orientation == "horizontal" else 0)
            potential_coords.append((r, c))

        # 3. Kiểm tra chồng chéo trực tiếp
        for r, c in potential_coords:
            if self.grid[r][c] != CellState.EMPTY:
                return False

        return True


    def place_ship(self, ship_obj, start_row, start_col, orientation):
        """Thực hiện đặt tàu lên bản đồ nếu vị trí hợp lệ."""
        if self._is_valid_placement(ship_obj.size, start_row, start_col, orientation):
            ship_obj.start_pos = (start_row, start_col)
            ship_obj.orientation = orientation
            for i in range(ship_obj.size):
                r = start_row + (i if orientation == "vertical" else 0)
                c = start_col + (i if orientation == "horizontal" else 0)
                self.grid[r][c] = CellState.SHIP
                ship_obj.coordinates.append((r, c))
            self.ships.append(ship_obj)
            return True
        return False

    def receive_shot(self, row, col):
        """Xử lý phát bắn và trả về kết quả cùng với đối tượng tàu bị ảnh hưởng."""
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return "Invalid", None

        current_state = self.grid[row][col]
        if current_state in [CellState.HIT, CellState.MISS, CellState.SUNK_SHIP]:
            return "Already_Shot", None

        if current_state == CellState.SHIP:
            self.grid[row][col] = CellState.HIT
            for ship in self.ships:
                if (row, col) in ship.coordinates:
                    if ship.take_hit():
                        for r_s, c_s in ship.coordinates:
                            self.grid[r_s][c_s] = CellState.SUNK_SHIP
                        return "Sunk", ship
                    else:
                        return "Hit", ship
        else: # EMPTY
            self.grid[row][col] = CellState.MISS
            return "Miss", None

    def get_remaining_ships(self):
        """Trả về danh sách các tàu chưa chìm."""
        return [ship for ship in self.ships if not ship.is_sunk]
            
    def print_board(self, title="", show_ships=True):
        """In bản đồ ra console một cách trực quan."""
        print(f"\n--- {title} ---")
        print("   " + " ".join([chr(ord('A') + i) for i in range(self.cols)]))
        print("  " + "-" * (self.cols * 2 + 1))
        for r_idx, row in enumerate(self.grid):
            print(f"{r_idx + 1:<2}|", end=" ")
            for cell in row:
                char_map = {
                    CellState.EMPTY: "~",
                    CellState.SHIP: "S" if show_ships else "~",
                    CellState.HIT: "X",
                    CellState.MISS: "O",
                    CellState.SUNK_SHIP: "#"
                }
                print(char_map.get(cell, "?"), end=" ")
            print("|")
        print("  " + "-" * (self.cols * 2 + 1))


# ==============================================================================
# SECTION 2: MODULE AI VÀ CÁC HÀM TIỆN ÍCH
# ==============================================================================

class SimpleAI:
    """AI đơn giản, bắn ngẫu nhiên vào các ô chưa từng bắn."""
    def __init__(self, rows=10, cols=10):
        self.possible_shots = [(r, c) for r in range(rows) for c in range(cols)]
        random.shuffle(self.possible_shots)

    def get_move(self):
        """Lấy một tọa độ để bắn."""
        return self.possible_shots.pop(0) if self.possible_shots else None

def clear_screen():
    """Xóa màn hình console để giao diện sạch sẽ hơn."""
    os.system('cls' if os.name == 'nt' else 'clear')

def ai_auto_place_ships(board, fleet_config):
    """Tự động đặt tàu cho AI một cách ngẫu nhiên và hợp lệ."""
    ships = [Ship(f["name"], f["size"]) for f in fleet_config]
    for ship in ships:
        placed = False
        while not placed:
            row = random.randint(0, board.rows - 1)
            col = random.randint(0, board.cols - 1)
            orientation = random.choice(["horizontal", "vertical"])
            placed = board.place_ship(ship, row, col, orientation)
    return ships

def display_fleet_status(ships, title):
    """In ra trạng thái của các tàu trong một hạm đội (còn lại/đã chìm)."""
    print(f"\n--- {title} ---")
    sorted_ships = sorted(ships, key=lambda s: s.size, reverse=True)
    for ship in sorted_ships:
        status = "ĐÃ CHÌM" if ship.is_sunk else "CÒN NỔI"
        print(f"- {ship.name:<11} (K.thước: {ship.size}): {status}")

class GameState:
    def __init__(self):
        self.player_board = Board()
        self.player_tracking_board = Board()
        self.ai_board = Board()
        self.ai_tracking_board = Board()
        self.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.current_turn = "Player"
        self.game_over = False
        self.winner = None

    def _ai_auto_place_ships(self):
        for ship in self.ai_fleet:
            placed = False
            while not placed:
                r = random.randint(0, self.ai_board.rows-1)
                c = random.randint(0, self.ai_board.cols-1)
                orientation = random.choice(["horizontal","vertical"])
                placed = self.ai_board.place_ship(ship, r,c,orientation)

    def player_shot(self, row, col):
        if self.game_over or self.current_turn != "Player":
            return "Not_Player_Turn"

        result, ship = self.ai_board.receive_shot(row, col)
        if result in ["Hit","Sunk"]:
            self.player_tracking_board.grid[row][col] = CellState.HIT
            if result == "Sunk":
                for r, c in ship.coordinates:
                    self.player_tracking_board.grid[r][c] = CellState.SUNK_SHIP
            if all(s.is_sunk for s in self.ai_board.ships):
                self.game_over = True
                self.winner = "Player"
                return "Win"
        elif result == "Miss":
            self.player_tracking_board.grid[row][col] = CellState.MISS
        elif result in ["Already_Shot","Invalid"]:
            return result

        self.current_turn = "AI"
        return result

    def ai_shot(self, ai_module):
        if self.game_over or self.current_turn != "AI":
            return "Not_AI_Turn"

        while True:
            r, c = ai_module.choose_move()
            result, ship = self.player_board.receive_shot(r, c)

            sunk_len = ship.size if (result == "Sunk" and ship) else None
            if hasattr(ai_module, "feedback"):
                ai_module.feedback((r, c), result, sunk_ship_len=sunk_len)

            if result in ["Already_Shot", "Invalid"]:
                continue  # chọn lại nếu nước đi không hợp lệ
            break

        # --- Cập nhật tracking board ---
        if result in ["Hit", "Sunk"]:
            self.ai_tracking_board.grid[r][c] = CellState.HIT
            if result == "Sunk":
                for r2, c2 in ship.coordinates:
                    self.ai_tracking_board.grid[r2][c2] = CellState.SUNK_SHIP

            # ✅ Check toàn bộ tàu của Player
            if all(s.is_sunk for s in self.player_board.ships):
                self.game_over = True
                self.winner = "AI"
                return "Win"

        elif result == "Miss":
            self.ai_tracking_board.grid[r][c] = CellState.MISS

        # 👉 Đổi lượt nếu game chưa kết thúc
        if not self.game_over:
            self.current_turn = "Player"

        return result
    





