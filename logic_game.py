# logic_game.py
import random

class CellState:
    EMPTY = 0
    SHIP = 1
    HIT = 2
    MISS = 3
    SUNK_SHIP = 4

class Ship:
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

    def reset(self):
        self.hits_taken = 0
        self.is_sunk = False
        self.coordinates = []
        self.orientation = None
        self.start_pos = None

FLEET_CONFIG = [
    {"name": "Carrier", "size": 5},
    {"name": "Battleship", "size": 4},
    {"name": "Cruiser", "size": 3},
    {"name": "Submarine", "size": 3},
    {"name": "Destroyer", "size": 2},
]

class Board:
    def __init__(self, rows=10, cols=10):
        self.rows = rows
        self.cols = cols
        self.grid = [[CellState.EMPTY for _ in range(cols)] for _ in range(rows)]
        self.ships = []

    def reset_board(self):
        self.grid = [[CellState.EMPTY for _ in range(self.cols)] for _ in range(self.rows)]
        for ship in self.ships:
            ship.reset()
        self.ships = []

    def _is_valid_placement(self, ship_obj, start_row, start_col, orientation):
        if orientation == "horizontal":
            if start_col + ship_obj.size > self.cols: return False
        else:
            if start_row + ship_obj.size > self.rows: return False

        potential_coords = []
        for i in range(ship_obj.size):
            if orientation == "horizontal":
                potential_coords.append((start_row, start_col + i))
            else:
                potential_coords.append((start_row + i, start_col))

        for r, c in potential_coords:
            if self.grid[r][c] == CellState.SHIP: return False
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if self.grid[nr][nc] == CellState.SHIP:
                            return False
        return True

    def place_ship(self, ship_obj, start_row, start_col, orientation):
        if not self._is_valid_placement(ship_obj, start_row, start_col, orientation):
            return False
        coords = []
        for i in range(ship_obj.size):
            if orientation == "horizontal":
                r, c = start_row, start_col+i
            else:
                r, c = start_row+i, start_col
            self.grid[r][c] = CellState.SHIP
            coords.append((r,c))
        ship_obj.coordinates = coords
        ship_obj.start_pos = (start_row, start_col)
        ship_obj.orientation = orientation
        self.ships.append(ship_obj)
        return True

    def receive_shot(self, row, col):
        if not (0 <= row < self.rows and 0 <= col < self.cols):
            return "Invalid", None
        state = self.grid[row][col]
        if state in [CellState.HIT, CellState.MISS, CellState.SUNK_SHIP]:
            return "Already_Shot", None
        if state == CellState.SHIP:
            self.grid[row][col] = CellState.HIT
            hit_ship = None
            for ship in self.ships:
                if (row, col) in ship.coordinates:
                    hit_ship = ship
                    break
            if hit_ship:
                if hit_ship.take_hit():
                    for r,c in hit_ship.coordinates:
                        self.grid[r][c] = CellState.SUNK_SHIP
                    return "Sunk", hit_ship.name
                else:
                    return "Hit", hit_ship.name
            return "Hit", None
        else:
            self.grid[row][col] = CellState.MISS
            return "Miss", None

    def print_board(self, show_ships=True):
        print("   A B C D E F G H I J")
        for r_idx, row in enumerate(self.grid):
            print(f"{r_idx+1:2d}|", end=" ")
            for cell in row:
                if cell == CellState.EMPTY: print("~", end=" ")
                elif cell == CellState.SHIP: print("S", end=" ") if show_ships else print("~", end=" ")
                elif cell == CellState.HIT: print("X", end=" ")
                elif cell == CellState.MISS: print("O", end=" ")
                elif cell == CellState.SUNK_SHIP: print("D", end=" ")
            print()

class GameState:
    def __init__(self):
        self.player_board = Board()
        self.player_tracking_board = Board()
        self.ai_board = Board()
        self.ai_tracking_board = Board()
        self.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.current_turn = "Player"
        self.turn_count = 0
        self.game_over = False
        self.winner = None

    def setup_game(self):
        self.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.player_board.reset_board()
        # đặt cứng để test nhanh
        self.player_board.place_ship(self.player_fleet[0], 0,0,"horizontal")
        self.player_board.place_ship(self.player_fleet[1], 2,0,"vertical")
        self.player_board.place_ship(self.player_fleet[2], 0,7,"vertical")
        self.player_board.place_ship(self.player_fleet[3], 5,5,"horizontal")
        self.player_board.place_ship(self.player_fleet[4], 9,2,"horizontal")
        print("Player board:")
        self.player_board.print_board(show_ships=True)

        self.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.ai_board.reset_board()
        self._ai_auto_place_ships()
        print("\nAI board (debug only):")
        self.ai_board.print_board(show_ships=True)

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
        result, ship_name = self.ai_board.receive_shot(row,col)
        if result in ["Hit","Sunk"]:
            self.player_tracking_board.grid[row][col] = CellState.HIT
            if result == "Sunk":
                for ship in self.ai_fleet:
                    if ship.name == ship_name:
                        for r,c in ship.coordinates:
                            self.player_tracking_board.grid[r][c] = CellState.SUNK_SHIP
            if all(ship.is_sunk for ship in self.ai_fleet):
                self.game_over = True
                self.winner = "Player"
                return "Win"
        elif result == "Miss":
            self.player_tracking_board.grid[row][col] = CellState.MISS
        elif result in ["Already_Shot","Invalid"]:
            return result
        self.current_turn = "AI"
        self.turn_count += 1
        return result

    def ai_shot(self, ai_module):
        if self.game_over or self.current_turn != "AI":
            return "Not_AI_Turn"
        r,c = ai_module.choose_move()
        result, ship_name = self.player_board.receive_shot(r,c)
        if result in ["Hit","Sunk"]:
            self.ai_tracking_board.grid[r][c] = CellState.HIT
            if result == "Sunk":
                for ship in self.player_fleet:
                    if ship.name == ship_name:
                        for r2,c2 in ship.coordinates:
                            self.ai_tracking_board.grid[r2][c2] = CellState.SUNK_SHIP
            if all(ship.is_sunk for ship in self.player_fleet):
                self.game_over = True
                self.winner = "AI"
                return "Win"
        elif result == "Miss":
            self.ai_tracking_board.grid[r][c] = CellState.MISS
        elif result in ["Already_Shot","Invalid"]:
            return result
        self.current_turn = "Player"
        self.turn_count += 1
        return result
