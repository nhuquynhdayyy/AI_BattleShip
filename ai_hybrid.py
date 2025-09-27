# FILE: ai_hybrid.py
# PHIÊN BẢN IQ 100 - TẬP TRUNG VÀO LOGIC "SĂN & DIỆT"

import random
from logic_game import CellState

class HybridAI:
    def __init__(self, board_size=10, ships_config=None):
        self.board_size = board_size
        # Danh sách tất cả các ô có thể bắn, được xáo trộn
        self.possible_shots = [(r, c) for r in range(board_size) for c in range(board_size)]
        random.shuffle(self.possible_shots)
        
        # --- TRẠNG THÁI CỐT LÕI CỦA AI ---
        self.mode = 'hunt'  # 'hunt' (săn) hoặc 'target' (diệt)
        self.target_queue = [] # Các ô ưu tiên bắn khi ở chế độ target
        self.hits = []      # Các ô đã trúng của con tàu đang bị tấn công

    def get_move(self, tracking_board, remaining_ships):
        """
        Chọn nước đi tiếp theo một cách thông minh.
        ƯU TIÊN 1: Chế độ TARGET (nếu có mục tiêu).
        ƯU TIÊN 2: Chế độ HUNT (dùng bản đồ xác suất).
        """
        # --- ƯU TIÊN 1: CHẾ ĐỘ TARGET ---
        # Nếu có mục tiêu trong hàng đợi, hãy xử lý nó trước
        while self.target_queue:
            move = self.target_queue.pop(0)
            # Nếu ô này hợp lệ (chưa bị bắn), hãy chọn nó
            if move in self.possible_shots:
                self.possible_shots.remove(move)
                return move
        
        # Nếu hàng đợi mục tiêu rỗng nhưng vẫn còn 'hits', nghĩa là có lỗi logic.
        # Quay lại chế độ HUNT để tự sửa chữa.
        if not self.target_queue and self.hits:
            self.mode = 'hunt'
            self.hits = []

        # --- ƯU TIÊN 2: CHẾ ĐỘ HUNT ---
        # Nếu không có mục tiêu, hãy tìm ô tốt nhất để bắt đầu cuộc săn mới
        scores = self._compute_probability_grid(tracking_board, remaining_ships)
        
        best_move = None
        max_score = -1

        # Tìm các ô có điểm cao nhất trong số các ô chưa bắn
        # Lặp qua danh sách đã xáo trộn để đảm bảo tính ngẫu nhiên khi có nhiều ô bằng điểm
        for r, c in self.possible_shots:
            if scores[r][c] > max_score:
                max_score = scores[r][c]
                best_move = (r, c)
        
        # Nếu không tìm thấy ô nào (rất hiếm), bắn ngẫu nhiên
        if best_move is None and self.possible_shots:
            best_move = self.possible_shots[0]

        if best_move in self.possible_shots:
            self.possible_shots.remove(best_move)
        
        return best_move

    def report_result(self, move, result):
        """
        Nhận phản hồi từ game để cập nhật trạng thái và chiến thuật.
        Đây là "bộ não" quyết định của AI.
        """
        if result == "Hit":
            # 1. Chuyển sang chế độ TARGET
            self.mode = 'target'
            # 2. Ghi nhận điểm bắn trúng
            self.hits.append(move)
            # 3. Thêm các ô xung quanh (trên, dưới, trái, phải) vào hàng đợi mục tiêu
            r, c = move
            potential_targets = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
            for target in potential_targets:
                # Chỉ thêm nếu ô nằm trong bản đồ và chưa từng được thêm vào hàng đợi
                if 0 <= target[0] < self.board_size and 0 <= target[1] < self.board_size:
                    if target not in self.target_queue:
                        self.target_queue.append(target)
            
            # Nếu đã có 2 điểm trúng trở lên, AI có thể suy ra hướng của tàu
            if len(self.hits) >= 2:
                self._refine_target_queue()

        elif result == "Sunk":
            # 1. Mục tiêu đã bị hạ, reset hoàn toàn để bắt đầu cuộc săn mới
            self.mode = 'hunt'
            self.target_queue = []
            self.hits = []
        
        elif result == "Miss":
            # Nếu đang ở chế độ target mà bắn trượt, không cần làm gì đặc biệt.
            # Vòng lặp `get_move` sẽ tự động thử các ô khác trong hàng đợi.
            pass

    def _refine_target_queue(self):
        """
        Khi đã có 2 điểm trúng, AI sẽ thông minh hơn bằng cách chỉ bắn theo đường thẳng.
        """
        first_hit = self.hits[0]
        last_hit = self.hits[-1]
        
        # Xác định hướng (ngang hay dọc)
        is_horizontal = first_hit[0] == last_hit[0]
        
        new_queue = []
        if is_horizontal:
            row = first_hit[0]
            min_col = min(h[1] for h in self.hits)
            max_col = max(h[1] for h in self.hits)
            # Thêm 2 đầu của đường thẳng
            new_queue.append((row, min_col - 1))
            new_queue.append((row, max_col + 1))
        else: # Dọc
            col = first_hit[1]
            min_row = min(h[0] for h in self.hits)
            max_row = max(h[0] for h in self.hits)
            # Thêm 2 đầu của đường thẳng
            new_queue.append((min_row - 1, col))
            new_queue.append((max_row + 1, col))
            
        # Cập nhật hàng đợi với các mục tiêu thông minh hơn
        self.target_queue = [
            t for t in new_queue 
            if 0 <= t[0] < self.board_size and 0 <= t[1] < self.board_size
        ]

    def _compute_probability_grid(self, tracking_board, remaining_ships):
        rows, cols = self.board_size, self.board_size
        scores = [[0] * cols for _ in range(rows)]
        
        # Nếu không còn tàu thì không cần tính
        if not remaining_ships: return scores
        ship_lengths = [s.size for s in remaining_ships if not s.is_sunk]

        for length in ship_lengths:
            for r in range(rows):
                for c in range(cols):
                    # Kiểm tra đặt ngang
                    if c + length <= cols:
                        if all(tracking_board.grid[r][c+i] == CellState.EMPTY for i in range(length)):
                            for i in range(length): scores[r][c+i] += 1
                    # Kiểm tra đặt dọc
                    if r + length <= rows:
                        if all(tracking_board.grid[r+i][c] == CellState.EMPTY for i in range(length)):
                            for i in range(length): scores[r+i][c] += 1
        return scores