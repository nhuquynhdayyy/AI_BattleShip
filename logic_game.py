# # logic_game.py
# import random

# class CellState:
#     EMPTY = 0
#     SHIP = 1
#     HIT = 2
#     MISS = 3
#     SUNK_SHIP = 4

# class Ship:
#     def __init__(self, name, size):
#         self.name = name
#         self.size = size
#         self.hits_taken = 0
#         self.is_sunk = False
#         self.coordinates = []
#         self.orientation = None
#         self.start_pos = None

#     def take_hit(self):
#         self.hits_taken += 1
#         if self.hits_taken >= self.size:
#             self.is_sunk = True
#             return True
#         return False

#     def reset(self):
#         self.hits_taken = 0
#         self.is_sunk = False
#         self.coordinates = []
#         self.orientation = None
#         self.start_pos = None

# FLEET_CONFIG = [
#     {"name": "Carrier", "size": 5},
#     {"name": "Battleship", "size": 4},
#     {"name": "Cruiser", "size": 3},
#     {"name": "Submarine", "size": 3},
#     {"name": "Destroyer", "size": 2},
# ]

# class Board:
#     def __init__(self, rows=10, cols=10):
#         self.rows = rows
#         self.cols = cols
#         self.grid = [[CellState.EMPTY for _ in range(cols)] for _ in range(rows)]
#         self.ships = []

#     def reset_board(self):
#         self.grid = [[CellState.EMPTY for _ in range(self.cols)] for _ in range(self.rows)]
#         for ship in self.ships:
#             ship.reset()
#         self.ships = []

#     # def _is_valid_placement(self, ship_obj, start_row, start_col, orientation):
#     #     if orientation == "horizontal":
#     #         if start_col + ship_obj.size > self.cols: return False
#     #     else:
#     #         if start_row + ship_obj.size > self.rows: return False

#     #     potential_coords = []
#     #     for i in range(ship_obj.size):
#     #         if orientation == "horizontal":
#     #             potential_coords.append((start_row, start_col + i))
#     #         else:
#     #             potential_coords.append((start_row + i, start_col))

#     #     for r, c in potential_coords:
#     #         if self.grid[r][c] == CellState.SHIP: return False
#     #         for dr in [-1,0,1]:
#     #             for dc in [-1,0,1]:
#     #                 nr, nc = r+dr, c+dc
#     #                 if 0 <= nr < self.rows and 0 <= nc < self.cols:
#     #                     if self.grid[nr][nc] == CellState.SHIP:
#     #                         return False
#     #     return True

#     def _is_valid_placement(self, ship_obj, start_row, start_col, orientation):
#         if orientation == "horizontal":
#             if start_col + ship_obj.size > self.cols: return False
#         else:
#             if start_row + ship_obj.size > self.rows: return False

#         potential_coords = []
#         for i in range(ship_obj.size):
#             if orientation == "horizontal":
#                 potential_coords.append((start_row, start_col + i))
#             else:
#                 potential_coords.append((start_row + i, start_col))

#         # ❌ Bỏ kiểm tra 8 ô xung quanh, chỉ check chồng trực tiếp
#         for r, c in potential_coords:
#             if self.grid[r][c] == CellState.SHIP:
#                 return False
#         return True


#     def place_ship(self, ship_obj, start_row, start_col, orientation):
#         if not self._is_valid_placement(ship_obj, start_row, start_col, orientation):
#             return False
#         coords = []
#         for i in range(ship_obj.size):
#             if orientation == "horizontal":
#                 r, c = start_row, start_col+i
#             else:
#                 r, c = start_row+i, start_col
#             self.grid[r][c] = CellState.SHIP
#             coords.append((r,c))
#         ship_obj.coordinates = coords
#         ship_obj.start_pos = (start_row, start_col)
#         ship_obj.orientation = orientation
#         self.ships.append(ship_obj)
#         return True

#     def receive_shot(self, row, col):
#         if not (0 <= row < self.rows and 0 <= col < self.cols):
#             return "Invalid", None
#         state = self.grid[row][col]
#         if state in [CellState.HIT, CellState.MISS, CellState.SUNK_SHIP]:
#             return "Already_Shot", None
#         if state == CellState.SHIP:
#             self.grid[row][col] = CellState.HIT
#             hit_ship = None
#             for ship in self.ships:
#                 if (row, col) in ship.coordinates:
#                     hit_ship = ship
#                     break
#             if hit_ship:
#                 if hit_ship.take_hit():
#                     for r,c in hit_ship.coordinates:
#                         self.grid[r][c] = CellState.SUNK_SHIP
#                     return "Sunk", hit_ship.name
#                 else:
#                     return "Hit", hit_ship.name
#             return "Hit", None
#         else:
#             self.grid[row][col] = CellState.MISS
#             return "Miss", None

#     def print_board(self, show_ships=True):
#         print("   A B C D E F G H I J")
#         for r_idx, row in enumerate(self.grid):
#             print(f"{r_idx+1:2d}|", end=" ")
#             for cell in row:
#                 if cell == CellState.EMPTY: print("~", end=" ")
#                 elif cell == CellState.SHIP: print("S", end=" ") if show_ships else print("~", end=" ")
#                 elif cell == CellState.HIT: print("X", end=" ")
#                 elif cell == CellState.MISS: print("O", end=" ")
#                 elif cell == CellState.SUNK_SHIP: print("D", end=" ")
#             print()

# class GameState:
#     def __init__(self):
#         self.player_board = Board()
#         self.player_tracking_board = Board()
#         self.ai_board = Board()
#         self.ai_tracking_board = Board()
#         self.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
#         self.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
#         self.current_turn = "Player"
#         self.turn_count = 0
#         self.game_over = False
#         self.winner = None

#     def setup_game(self):
#         self.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
#         self.player_board.reset_board()
#         # đặt cứng để test nhanh
#         self.player_board.place_ship(self.player_fleet[0], 0,0,"horizontal")
#         self.player_board.place_ship(self.player_fleet[1], 2,0,"vertical")
#         self.player_board.place_ship(self.player_fleet[2], 0,7,"vertical")
#         self.player_board.place_ship(self.player_fleet[3], 5,5,"horizontal")
#         self.player_board.place_ship(self.player_fleet[4], 9,2,"horizontal")
#         print("Player board:")
#         self.player_board.print_board(show_ships=True)

#         self.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
#         self.ai_board.reset_board()
#         self._ai_auto_place_ships()
#         print("\nAI board (debug only):")
#         self.ai_board.print_board(show_ships=True)

#     def _ai_auto_place_ships(self):
#         for ship in self.ai_fleet:
#             placed = False
#             while not placed:
#                 r = random.randint(0, self.ai_board.rows-1)
#                 c = random.randint(0, self.ai_board.cols-1)
#                 orientation = random.choice(["horizontal","vertical"])
#                 placed = self.ai_board.place_ship(ship, r,c,orientation)

#     def player_shot(self, row, col):
#         if self.game_over or self.current_turn != "Player":
#             return "Not_Player_Turn"
#         result, ship_name = self.ai_board.receive_shot(row,col)
#         if result in ["Hit","Sunk"]:
#             self.player_tracking_board.grid[row][col] = CellState.HIT
#             if result == "Sunk":
#                 for ship in self.ai_fleet:
#                     if ship.name == ship_name:
#                         for r,c in ship.coordinates:
#                             self.player_tracking_board.grid[r][c] = CellState.SUNK_SHIP
#             if all(ship.is_sunk for ship in self.ai_fleet):
#                 self.game_over = True
#                 self.winner = "Player"
#                 return "Win"
#         elif result == "Miss":
#             self.player_tracking_board.grid[row][col] = CellState.MISS
#         elif result in ["Already_Shot","Invalid"]:
#             return result
#         self.current_turn = "AI"
#         self.turn_count += 1
#         return result

#     def ai_shot(self, ai_module):
#         if self.game_over or self.current_turn != "AI":
#             return "Not_AI_Turn"
#         r,c = ai_module.choose_move()
#         result, ship_name = self.player_board.receive_shot(r,c)
#         if result in ["Hit","Sunk"]:
#             self.ai_tracking_board.grid[r][c] = CellState.HIT
#             if result == "Sunk":
#                 for ship in self.player_fleet:
#                     if ship.name == ship_name:
#                         for r2,c2 in ship.coordinates:
#                             self.ai_tracking_board.grid[r2][c2] = CellState.SUNK_SHIP
#             if all(ship.is_sunk for ship in self.player_fleet):
#                 self.game_over = True
#                 self.winner = "AI"
#                 return "Win"
#         elif result == "Miss":
#             self.ai_tracking_board.grid[r][c] = CellState.MISS
#         elif result in ["Already_Shot","Invalid"]:
#             return result
#         self.current_turn = "Player"
#         self.turn_count += 1
#         return result



# # FILE: logic_game.py
# import random
# from datetime import datetime

# # ==============================================================================
# # SECTION 1: CÁC LỚP LOGIC CỐT LÕI
# # ==============================================================================

# class CellState:
#     EMPTY = 0
#     SHIP = 1
#     HIT = 2
#     MISS = 3
#     SUNK_SHIP = 4

# FLEET_CONFIG = [
#     {"name": "Carrier", "size": 5},
#     {"name": "Battleship", "size": 4},
#     {"name": "Cruiser", "size": 3},
#     {"name": "Submarine", "size": 3},
#     {"name": "Destroyer", "size": 2},
# ]

# class Ship:
#     def __init__(self, name, size):
#         self.name = name
#         self.size = size
#         self.hits_taken = 0
#         self.is_sunk = False
#         self.coordinates = []
#         self.orientation = None
#         self.start_pos = None

#     def take_hit(self):
#         self.hits_taken += 1
#         if self.hits_taken >= self.size:
#             self.is_sunk = True
#             return True
#         return False

# class Board:
#     def __init__(self, rows=10, cols=10):
#         self.rows = rows
#         self.cols = cols
#         self.grid = [[CellState.EMPTY for _ in range(cols)] for _ in range(rows)]
#         self.ships = []

#     def _is_valid_placement(self, ship_size, start_row, start_col, orientation):
#         # Chỉ kiểm tra biên và chồng chéo
#         if orientation == "horizontal":
#             if start_col + ship_size > self.cols: return False
#         else:
#             if start_row + ship_size > self.rows: return False

#         for i in range(ship_size):
#             r = start_row + (i if orientation == "vertical" else 0)
#             c = start_col + (i if orientation == "horizontal" else 0)
#             if self.grid[r][c] != CellState.EMPTY:
#                 return False
#         return True

#     def place_ship(self, ship_obj, start_row, start_col, orientation):
#         if self._is_valid_placement(ship_obj.size, start_row, start_col, orientation):
#             ship_obj.start_pos = (start_row, start_col)
#             ship_obj.orientation = orientation
#             ship_obj.coordinates = []
#             for i in range(ship_obj.size):
#                 r = start_row + (i if orientation == "vertical" else 0)
#                 c = start_col + (i if orientation == "horizontal" else 0)
#                 self.grid[r][c] = CellState.SHIP
#                 ship_obj.coordinates.append((r, c))
#             self.ships.append(ship_obj)
#             return True
#         return False

#     def receive_shot(self, row, col):
#         if not (0 <= row < self.rows and 0 <= col < self.cols):
#             return "Invalid", None
#         state = self.grid[row][col]
#         if state in [CellState.HIT, CellState.MISS, CellState.SUNK_SHIP]:
#             return "Already_Shot", None
#         if state == CellState.SHIP:
#             self.grid[row][col] = CellState.HIT
#             for ship in self.ships:
#                 if (row, col) in ship.coordinates:
#                     if ship.take_hit():
#                         for r_s, c_s in ship.coordinates:
#                             self.grid[r_s][c_s] = CellState.SUNK_SHIP
#                         return "Sunk", ship
#                     else:
#                         return "Hit", ship
#         else:
#             self.grid[row][col] = CellState.MISS
#             return "Miss", None

# class GameState:
#     def __init__(self):
#         self.player_board = Board()
#         self.ai_board = Board()
#         self.player_tracking_board = Board()
#         self.ai_tracking_board = Board()
#         self.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
#         self.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
#         self.current_turn = "Player"
#         self.winner = None
#         self.game_over = False

#     def check_game_over(self):
#         if all(ship.is_sunk for ship in self.ai_fleet):
#             self.winner = "Player"
#             self.game_over = True
#             return True
#         if all(ship.is_sunk for ship in self.player_fleet):
#             self.winner = "AI"
#             self.game_over = True
#             return True
#         return False

#     def switch_turn(self):
#         self.current_turn = "AI" if self.current_turn == "Player" else "Player"

#     # ===== BỔ SUNG CHO CONSOLE + GUI =====
#     def player_shot(self, row, col):
#         if self.game_over or self.current_turn != "Player":
#             return "Not_Player_Turn"
#         result, ship = self.ai_board.receive_shot(row, col)
#         if result in ["Hit", "Sunk"]:
#             self.player_tracking_board.grid[row][col] = CellState.HIT
#             if result == "Sunk":
#                 for r, c in ship.coordinates:
#                     self.player_tracking_board.grid[r][c] = CellState.SUNK_SHIP
#         elif result == "Miss":
#             self.player_tracking_board.grid[row][col] = CellState.MISS
#         if result not in ["Already_Shot", "Invalid"]:
#             if self.check_game_over():
#                 return "Win"
#             self.switch_turn()
#         return result

#     def ai_shot(self, ai_module):
#         if self.game_over or self.current_turn != "AI":
#             return "Not_AI_Turn"
#         row, col = ai_module.choose_move()
#         result, ship = self.player_board.receive_shot(row, col)
#         if result in ["Hit", "Sunk"]:
#             self.ai_tracking_board.grid[row][col] = CellState.HIT
#             if result == "Sunk":
#                 for r, c in ship.coordinates:
#                     self.ai_tracking_board.grid[r][c] = CellState.SUNK_SHIP
#         elif result == "Miss":
#             self.ai_tracking_board.grid[row][col] = CellState.MISS
#         if result not in ["Already_Shot", "Invalid"]:
#             if self.check_game_over():
#                 return "Win"
#             self.switch_turn()
#         return result

# # ==============================================================================
# # SECTION 2: TIỆN ÍCH
# # ==============================================================================

# def ai_auto_place_ships(board, fleet):
#     for ship in fleet:
#         placed = False
#         for _ in range(100):
#             r = random.randint(0, board.rows - 1)
#             c = random.randint(0, board.cols - 1)
#             orientation = random.choice(["horizontal", "vertical"])
#             if board.place_ship(ship, r, c, orientation):
#                 placed = True
#                 break
#         if not placed:
#             print(f"⚠️ Không thể đặt {ship.name} cho AI!")

# def display_fleet_status(ships):
#     status_lines = []
#     for ship in sorted(ships, key=lambda s: s.size, reverse=True):
#         status = "ĐÃ CHÌM" if ship.is_sunk else "CÒN NỔI"
#         status_lines.append(f"- {ship.name:<11} (Size: {ship.size}): {status}")
#     return "\n".join(status_lines)

# class GameLogger:
#     def __init__(self):
#         timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
#         self.filename = f"battleship_log_{timestamp}.txt"
#         with open(self.filename, 'w', encoding='utf-8') as f:
#             f.write(f"===== BATTLESHIP LOG - START {timestamp} =====\n\n")

#     def log_event(self, message):
#         timestamp = datetime.now().strftime("%H:%M:%S")
#         with open(self.filename, 'a', encoding='utf-8') as f:
#             f.write(f"[{timestamp}] {message}\n")

#     def log_placements(self, player_name, board):
#         self.log_event(f"Vị trí đặt tàu của {player_name}:")
#         with open(self.filename, 'a', encoding='utf-8') as f:
#             for ship in board.ships:
#                 start_pos_str = f"{chr(ord('A')+ship.start_pos[1])}{ship.start_pos[0]+1}"
#                 f.write(f"  - {ship.name:<11} tại {start_pos_str}, Hướng: {ship.orientation}\n")

#     def log_shot(self, player_name, coords, result, ship=None):
#         r, c = coords
#         coord_str = f"{chr(ord('A')+c)}{r+1}"
#         msg = f"{player_name} bắn {coord_str} → {result}"
#         if result in ["Hit", "Sunk"] and ship:
#             msg += f" ({ship.name})"
#         self.log_event(msg)

#     def log_winner(self, winner_name):
#         self.log_event(f"🏆 Winner: {winner_name}")



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
        """Kiểm tra xem vị trí đặt tàu có hợp lệ không (trong biên, không chồng chéo, không tiếp xúc)."""
        if orientation == "horizontal":
            if not (0 <= start_row < self.rows and 0 <= start_col < self.cols and start_col + ship_size <= self.cols):
                return False
        else: # "vertical"
            if not (0 <= start_row < self.rows and 0 <= start_col < self.cols and start_row + ship_size <= self.rows):
                return False

        # Lấy danh sách tọa độ tiềm năng
        potential_coords = []
        for i in range(ship_size):
            r = start_row + (i if orientation == "vertical" else 0)
            c = start_col + (i if orientation == "horizontal" else 0)
            potential_coords.append((r, c))

        # Kiểm tra xung quanh các tọa độ tiềm năng
        for r, c in potential_coords:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    neighbor_row, neighbor_col = r + dr, c + dc
                    if 0 <= neighbor_row < self.rows and 0 <= neighbor_col < self.cols:
                        if self.grid[neighbor_row][neighbor_col] != CellState.EMPTY:
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





