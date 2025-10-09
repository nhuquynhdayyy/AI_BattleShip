# FILE: logic_game.py
# PHIÊN BẢN HOÀN THIỆN - TẬP TRUNG LOGIC CHUYỂN LƯỢT

import random

class CellState:
    EMPTY, SHIP, HIT, MISS, SUNK_SHIP = 0, 1, 2, 3, 4

FLEET_CONFIG = [
    {"name": "Carrier", "size": 5}, {"name": "Battleship", "size": 4},
    {"name": "Cruiser", "size": 3}, {"name": "Submarine", "size": 3},
    {"name": "Destroyer", "size": 2},
]

class Ship:
    def __init__(self, name, size):
        self.name, self.size = name, size
        self.hits_taken, self.is_sunk = 0, False
        self.coordinates, self.orientation, self.start_pos = [], None, None
    def take_hit(self):
        self.hits_taken += 1
        if self.hits_taken >= self.size: self.is_sunk = True
        return self.is_sunk

class Board:
    def __init__(self, rows=10, cols=10):
        self.rows, self.cols = rows, cols
        self.grid = [[CellState.EMPTY for _ in range(cols)] for _ in range(rows)]
        self.ships = []

    def _is_valid_placement(self, ship_size, r, c, orientation):
        coords = []
        for i in range(ship_size):
            row, col = r + (i if orientation == "vertical" else 0), c + (i if orientation == "horizontal" else 0)
            if not (0 <= row < self.rows and 0 <= col < self.cols): return False
            coords.append((row, col))
        for row, col in coords:
            if self.grid[row][col] != CellState.EMPTY: return False
        return True

    def place_ship(self, ship, r, c, orientation):
        if not self._is_valid_placement(ship.size, r, c, orientation): return False
        ship.orientation, ship.start_pos = orientation, (r, c)
        ship.coordinates = []
        for i in range(ship.size):
            row, col = r + (i if orientation == "vertical" else 0), c + (i if orientation == "horizontal" else 0)
            self.grid[row][col] = CellState.SHIP
            ship.coordinates.append((row, col))
        if ship not in self.ships: self.ships.append(ship)
        return True
    
    def receive_shot(self, r, c):
        if not (0 <= r < self.rows and 0 <= c < self.cols): return "Invalid", None
        cell = self.grid[r][c]
        if cell in [CellState.HIT, CellState.MISS, CellState.SUNK_SHIP]: return "Already_Shot", None
        ship_hit = self.find_ship_at(r, c)
        if ship_hit:
            self.grid[r][c] = CellState.HIT
            if ship_hit.take_hit():
                for r_s, c_s in ship_hit.coordinates: self.grid[r_s][c_s] = CellState.SUNK_SHIP
                return "Sunk", ship_hit
            return "Hit", ship_hit
        else:
            self.grid[r][c] = CellState.MISS
            return "Miss", None

    def find_ship_at(self, r, c):
        for ship in self.ships:
            if (r, c) in ship.coordinates: return ship
        return None

    def remove_ship(self, ship):
        if ship in self.ships:
            for r, c in ship.coordinates: self.grid[r][c] = CellState.EMPTY
            self.ships.remove(ship)
            ship.coordinates = []
            return True
        return False
    
    def get_remaining_ships(self):
        return [ship for ship in self.ships if not ship.is_sunk]

class GameState:
    def __init__(self):
        self.player_board = Board()
        self.ai_board = None
        self.player_tracking_board = Board()
        self.ai_tracking_board = Board()
        self.player_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.ai_fleet = [Ship(f["name"], f["size"]) for f in FLEET_CONFIG]
        self.current_turn = "Player"
        self.winner = None
        self.game_over = False

    def start_battle(self):
        self.ai_board = Board()
        for ship in self.ai_fleet:
            placed = False
            while not placed:
                r, c = random.randint(0, 9), random.randint(0, 9)
                orientation = random.choice(["horizontal", "vertical"])
                placed = self.ai_board.place_ship(ship, r, c, orientation)

    def player_shot(self, r, c):
        result, ship = self.ai_board.receive_shot(r, c)
        if result not in ["Invalid", "Already_Shot"]:
            if result in ["Hit", "Sunk"]:
                self.player_tracking_board.grid[r][c] = CellState.HIT
                if result == "Sunk":
                    for r_s, c_s in ship.coordinates: self.player_tracking_board.grid[r_s][c_s] = CellState.SUNK_SHIP
            else: # Miss
                self.player_tracking_board.grid[r][c] = CellState.MISS
            
            if self.check_game_over(): return "Win", ship
            if result == "Miss": self.switch_turn()
        return result, ship

    def ai_shot(self, ai_player):
        move = ai_player.get_move(self.ai_tracking_board, self.player_board.get_remaining_ships())
        if not move: return "No_Move", None, None
        
        r, c = move
        result, ship = self.player_board.receive_shot(r, c)
        
        if hasattr(ai_player, 'report_result'):
            ai_player.report_result(move, result)
        
        if result not in ["Invalid", "Already_Shot"]:
            if result in ["Hit", "Sunk"]:
                self.ai_tracking_board.grid[r][c] = CellState.HIT
                if result == "Sunk":
                     for r_s, c_s in ship.coordinates: self.ai_tracking_board.grid[r_s][c_s] = CellState.SUNK_SHIP
            else: # Miss
                self.ai_tracking_board.grid[r][c] = CellState.MISS

            if self.check_game_over(): return "Win", ship, move
            if result == "Miss": self.switch_turn()
        return result, ship, move

    def check_game_over(self):
        if all(s.is_sunk for s in self.ai_fleet):
            self.winner, self.game_over = "Player", True
        elif all(s.is_sunk for s in self.player_fleet):
            self.winner, self.game_over = "AI", True
        return self.game_over

    def switch_turn(self):
        self.current_turn = "AI" if self.current_turn == "Player" else "Player"