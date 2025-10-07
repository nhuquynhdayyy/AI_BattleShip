import random

class HeuristicAI:
    def __init__(self, board_size=10):
        self.board_size = board_size
        self.possible_shots = [(r, c) for r in range(board_size) for c in range(board_size)]
        random.shuffle(self.possible_shots)
        
        self.mode = 'hunt'
        self.target_queue = []

    def get_move(self, tracking_board, remaining_ships):
        # Ưu tiên chế độ diệt
        while self.target_queue:
            move = self.target_queue.pop(0)
            if move in self.possible_shots:
                self.possible_shots.remove(move)
                return move
        
        # Nếu hết mục tiêu, quay lại chế độ săn
        self.mode = 'hunt'
        
        # Săn ngẫu nhiên (phiên bản đơn giản)
        if self.possible_shots:
            move = self.possible_shots.pop(0)
            return move
        return None

    def report_result(self, move, result):
        if result == "Hit":
            self.mode = 'target'
            r, c = move
            # Thêm các ô xung quanh vào hàng đợi mục tiêu
            potential_targets = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
            for target in potential_targets:
                if 0 <= target[0] < self.board_size and 0 <= target[1] < self.board_size:
                    if target not in self.target_queue:
                        self.target_queue.append(target)
        
        elif result == "Sunk":
            # Khi tàu chìm, xóa sạch hàng đợi và quay lại săn
            self.target_queue = []
            self.mode = 'hunt'