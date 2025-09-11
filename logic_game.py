# FILE: logic_game.py
# PHIÊN BẢN HOÀN CHỈNH - KHÔNG LƯỢC BỎ LOGIC

import random
import os
from datetime import datetime

# ==============================================================================
# SECTION 1: CÁC LỚP LOGIC CỐT LÕI
# ==============================================================================

class CellState:
    """Định nghĩa các trạng thái của một ô."""
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
    """Đại diện cho một con tàu."""
    def __init__(self, name, size):
        self.name = name
        self.size = size
        self.hits_taken = 0
        self.is_sunk = False
        self.coordinates = []
        self.orientation = None
        self.start_pos = None

    def take_hit(self):
        self.hits_taken += 1
        if self.hits_taken >= self.size:
            self.is_sunk = True
            return True
        return False

class Board:
    """Quản lý bản đồ, đặt tàu, và xử lý phát bắn."""
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
        # 1. Kiểm tra không nằm ngoài biên (giữ nguyên)
        if orientation == "horizontal":
            if not (0 <= start_row < self.rows and 0 <= start_col < self.cols and start_col + ship_size <= self.cols):
                return False
        else: # "vertical"
            if not (0 <= start_row < self.rows and 0 <= start_col < self.cols and start_row + ship_size <= self.rows):
                return False

        # 2. Lấy danh sách tọa độ tiềm năng (giữ nguyên)
        potential_coords = []
        for i in range(ship_size):
            r = start_row + (i if orientation == "vertical" else 0)
            c = start_col + (i if orientation == "horizontal" else 0)
            potential_coords.append((r, c))

        # 3. *** THAY ĐỔI QUAN TRỌNG ***
        # Chỉ kiểm tra chồng chéo trực tiếp, không kiểm tra các ô xung quanh
        for r, c in potential_coords:
            # Nếu ô đó đã có tàu (không phải EMPTY) thì không hợp lệ
            if self.grid[r][c] != CellState.EMPTY:
                return False
                
        return True # Nếu không có ô nào bị chồng chéo, vị trí này là hợp lệ

    def place_ship(self, ship_obj, start_row, start_col, orientation):
        if self._is_valid_placement(ship_obj.size, start_row, start_col, orientation):
            ship_obj.start_pos = (start_row, start_col)
            ship_obj.orientation = orientation
            ship_obj.coordinates = [] # Đảm bảo tọa độ cũ được xóa
            for i in range(ship_obj.size):
                r = start_row + (i if orientation == "vertical" else 0)
                c = start_col + (i if orientation == "horizontal" else 0)
                self.grid[r][c] = CellState.SHIP
                ship_obj.coordinates.append((r, c))
            self.ships.append(ship_obj)
            return True
        return False

    def receive_shot(self, row, col):
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
        else:
            self.grid[row][col] = CellState.MISS
            return "Miss", None

class GameState:
    """Lớp quản lý trạng thái tổng thể của trò chơi."""
    def __init__(self):
        self.player_board = Board()
        self.ai_board = Board()
        self.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.current_turn = "Player"
        self.winner = None

    def check_game_over(self):
        """Kiểm tra xem game đã kết thúc chưa và ai là người chiến thắng."""
        if all(ship.is_sunk for ship in self.ai_fleet):
            self.winner = "Player"
            return True
        if all(ship.is_sunk for ship in self.player_fleet):
            self.winner = "AI"
            return True
        return False
        
    def switch_turn(self):
        """Chuyển lượt chơi."""
        self.current_turn = "AI" if self.current_turn == "Player" else "Player"

# ==============================================================================
# SECTION 2: CÁC HÀM TIỆN ÍCH ĐƯỢC MANG VÀO ĐÂY
# ==============================================================================
# Các hàm này không phải là một phần của lớp nào, nhưng có thể được gọi từ
# các file khác (như gui_game.py) để thực hiện các tác vụ cụ thể.

def ai_auto_place_ships(board, fleet):
    """Tự động đặt tàu cho AI một cách ngẫu nhiên và hợp lệ."""
    for ship in fleet:
        placed = False
        # Tăng số lần thử để tránh treo game nếu không tìm được vị trí
        for _ in range(100): 
            row = random.randint(0, board.rows - 1)
            col = random.randint(0, board.cols - 1)
            orientation = random.choice(["horizontal", "vertical"])
            if board.place_ship(ship, row, col, orientation):
                placed = True
                break
        if not placed:
            # Xử lý trường hợp không thể đặt tàu, có thể cần reset và thử lại
            print(f"Cảnh báo: Không thể đặt tàu {ship.name} cho AI. Bố cục có thể không đầy đủ.")


def display_fleet_status(ships):
    """Tạo ra một chuỗi văn bản mô tả trạng thái hạm đội."""
    status_lines = []
    sorted_ships = sorted(ships, key=lambda s: s.size, reverse=True)
    for ship in sorted_ships:
        status = "ĐÃ CHÌM" if ship.is_sunk else "CÒN NỔI"
        status_lines.append(f"- {ship.name:<11} (Size: {ship.size}): {status}")
    return "\n".join(status_lines)

class GameLogger:
    def __init__(self):
        """Khởi tạo logger, tạo một file log duy nhất dựa trên thời gian."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = f"battleship_log_{timestamp}.txt"
        with open(self.filename, 'w', encoding='utf-8') as f:
            f.write(f"===== BATTLESHIP LOG - BẮT ĐẦU LÚC: {timestamp} =====\n\n")

    def log_event(self, message):
        """Ghi một sự kiện chung chung vào file log với dấu thời gian."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(self.filename, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def log_placements(self, player_name, board):
        """Ghi lại vị trí đặt tàu ban đầu của một người chơi."""
        self.log_event(f"Vị trí đặt tàu của {player_name}:")
        with open(self.filename, 'a', encoding='utf-8') as f:
            for ship in board.ships:
                start_pos_str = f"{chr(ord('A') + ship.start_pos[1])}{ship.start_pos[0] + 1}"
                f.write(f"  - {ship.name:<11} (Size: {ship.size}) tại {start_pos_str}, Hướng: {ship.orientation}\n")
            f.write("\n")

    def log_shot(self, player_name, coords, result, affected_ship=None):
        """Ghi lại một phát bắn."""
        row, col = coords
        coord_str = f"{chr(ord('A') + col)}{row + 1}"
        message = f"{player_name} bắn vào {coord_str}. Kết quả: {result}."
        if result in ["Hit", "Sunk"] and affected_ship:
            message += f" (Tàu: {affected_ship.name})"
        self.log_event(message)

    def log_winner(self, winner_name):
        """Ghi lại người chiến thắng và kết thúc log."""
        self.log_event("="*40)
        self.log_event(f"TRÒ CHƠI KẾT THÚC! NGƯỜI CHIẾN THẮNG: {winner_name}")
        self.log_event("="*40)