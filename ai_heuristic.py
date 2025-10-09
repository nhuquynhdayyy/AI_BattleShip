# FILE: ai_heuristic.py (Cấp độ Trung bình - Cải thiện)

import random
from collections import deque
from logic_game import CellState

class HeuristicAI:
    def __init__(self, board_size=10):
        self.board_size = board_size
        self.possible_shots = {(r, c) for r in range(board_size) for c in range(board_size)} # Dùng set cho hiệu quả hơn
        
        # --- TRẠNG THÁI CỐT LÕI CỦA AI ---
        self.mode = 'hunt'  # 'hunt' (săn) hoặc 'target' (diệt)
        self.target_queue = deque() # Hàng đợi các ô ưu tiên bắn khi ở chế độ target
        self.hits = []      # Các ô đã trúng của con tàu đang bị tấn công (chưa chìm)
        self.last_oriented = None # Hướng suy luận của tàu đang bị tấn công ('h' hoặc 'v')

        # Chiến lược săn cho chế độ HUNT: Parity (xen kẽ)
        # Sẽ ưu tiên bắn các ô có tổng tọa độ chẵn (0) trước, sau đó mới đến lẻ (1)
        self.hunt_parity = 0 # Bắt đầu với parity 0 ((r+c)%2 == 0)
        self.parity_shots_0 = [(r,c) for r in range(board_size) for c in range(board_size) if (r+c)%2 == 0]
        self.parity_shots_1 = [(r,c) for r in range(board_size) for c in range(board_size) if (r+c)%2 == 1]
        random.shuffle(self.parity_shots_0)
        random.shuffle(self.parity_shots_1)


    def get_move(self, tracking_board, remaining_ships):
        """
        Chọn nước đi tiếp theo một cách thông minh.
        ƯU TIÊN 1: Chế độ TARGET (nếu có mục tiêu hợp lệ).
        ƯU TIÊN 2: Chế độ HUNT (dùng chiến lược Parity).
        """
        # --- ƯU TIÊN 1: CHẾ ĐỘ TARGET ---
        # Làm sạch hàng đợi mục tiêu trước
        self._prune_target_queue(tracking_board)

        while self.target_queue:
            move = self.target_queue.popleft() # Dùng popleft() cho deque
            if move in self.possible_shots: # Đảm bảo chưa bắn ô này
                self.possible_shots.remove(move)
                return move
        
        # Nếu hàng đợi mục tiêu rỗng nhưng vẫn còn 'hits',
        # nghĩa là các mục tiêu cũ đã bị bắn hết hoặc không còn hợp lệ.
        # Thử tái tạo lại hàng đợi target hoặc chuyển về hunt.
        if self.hits and not self.target_queue:
            self._reseed_target_queue(tracking_board)
            self._prune_target_queue(tracking_board) # Prune lại sau khi reseed
            while self.target_queue:
                m = self.target_queue.popleft()
                if m in self.possible_shots:
                    self.possible_shots.remove(m)
                    return m
            # Nếu sau khi reseed mà hàng đợi vẫn rỗng, reset trạng thái target và quay về hunt.
            self.mode = 'hunt'
            self.hits.clear()
            self.last_oriented = None


        # --- ƯU TIÊN 2: CHẾ ĐỘ HUNT ---
        self.mode = 'hunt'
        best_move = None

        # Săn theo Parity (ưu tiên parity hiện tại)
        if self.hunt_parity == 0:
            while self.parity_shots_0:
                move = self.parity_shots_0.pop(0)
                if move in self.possible_shots and tracking_board.grid[move[0]][move[1]] == CellState.EMPTY:
                    best_move = move
                    break
            if not best_move and self.parity_shots_1: # Nếu hết parity 0, chuyển sang parity 1
                self.hunt_parity = 1
                while self.parity_shots_1:
                    move = self.parity_shots_1.pop(0)
                    if move in self.possible_shots and tracking_board.grid[move[0]][move[1]] == CellState.EMPTY:
                        best_move = move
                        break
        else: # hunt_parity == 1
            while self.parity_shots_1:
                move = self.parity_shots_1.pop(0)
                if move in self.possible_shots and tracking_board.grid[move[0]][move[1]] == CellState.EMPTY:
                    best_move = move
                    break
            if not best_move and self.parity_shots_0: # Nếu hết parity 1, chuyển sang parity 0
                self.hunt_parity = 0
                while self.parity_shots_0:
                    move = self.parity_shots_0.pop(0)
                    if move in self.possible_shots and tracking_board.grid[move[0]][move[1]] == CellState.EMPTY:
                        best_move = move
                        break

        # Fallback cuối cùng: bắn ngẫu nhiên từ possible_shots nếu mọi thứ khác thất bại
        if best_move is None and self.possible_shots:
            move = random.choice(list(self.possible_shots))
            best_move = move
            # Đảm bảo loại bỏ khỏi danh sách parity nếu nó được chọn ngẫu nhiên
            if move in self.parity_shots_0: self.parity_shots_0.remove(move)
            if move in self.parity_shots_1: self.parity_shots_1.remove(move)


        if best_move in self.possible_shots:
            self.possible_shots.remove(best_move)
        
        return best_move

    def report_result(self, move, result):
        """
        Nhận phản hồi từ game để cập nhật trạng thái và chiến thuật.
        """
        if result == "Hit":
            self.mode = 'target'
            self.hits.append(move)
            self._refine_orientation() # Cập nhật hướng nếu có thể
            self._grow_target_queue_from_hits() # Mở rộng hàng đợi dựa trên các hits

        elif result == "Sunk":
            self.mode = 'hunt'
            self.target_queue.clear()
            self.hits.clear()
            self.last_oriented = None
            # Reset parity logic (nếu muốn) hoặc để nó tiếp tục từ điểm hiện tại

        elif result == "Miss":
            pass # Hàng đợi target sẽ tự được prune ở lượt tiếp theo

    # --------- Hàm tiện ích cho TARGET mode ---------
    def _neighbors4(self, r, c):
        """Trả về các ô láng giềng 4 chiều."""
        yield r-1, c; yield r+1, c; yield r, c-1; yield r, c+1

    def _in_bounds(self, r, c):
        """Kiểm tra ô có nằm trong giới hạn bản đồ không."""
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _prune_target_queue(self, tracking_board):
        """
        Loại bỏ các mục tiêu không còn hợp lệ khỏi hàng đợi.
        """
        cleaned_queue = deque()
        for r, c in self.target_queue:
            if self._in_bounds(r, c) and tracking_board.grid[r][c] == CellState.EMPTY and ((r,c) in self.possible_shots):
                cleaned_queue.append((r, c))
        self.target_queue = cleaned_queue

    def _refine_orientation(self):
        """
        Suy luận hướng của con tàu đang bị tấn công nếu có ít nhất 2 điểm trúng.
        """
        if len(self.hits) < 2: return
        
        sorted_hits = sorted(self.hits) 
        r0, c0 = sorted_hits[0]
        r1, c1 = sorted_hits[1]

        if r0 == r1: # Cùng hàng -> ngang
            self.last_oriented = 'h'
        elif c0 == c1: # Cùng cột -> dọc
            self.last_oriented = 'v'
        
    def _grow_target_queue_from_hits(self):
        """
        Mở rộng hàng đợi mục tiêu dựa trên các điểm HIT hiện có và hướng suy luận.
        """
        if not self.hits: return
        
        hits_sorted = sorted(self.hits)
        candidates = set() 

        if self.last_oriented == 'h': # Đã xác định là ngang
            row = hits_sorted[0][0]
            min_col = min(h[1] for h in hits_sorted)
            max_col = max(h[1] for h in hits_sorted)
            candidates.add((row, min_col - 1)) 
            candidates.add((row, max_col + 1)) 
        elif self.last_oriented == 'v': # Đã xác định là dọc
            col = hits_sorted[0][1]
            min_row = min(h[0] for h in hits_sorted)
            max_row = max(h[0] for h in hits_sorted)
            candidates.add((min_row - 1, col)) 
            candidates.add((max_row + 1, col)) 
        else: # Chưa xác định được hướng (chỉ có 1 HIT hoặc HIT chéo)
            for r, c in hits_sorted:
                for nr, nc in self._neighbors4(r, c):
                    candidates.add((nr, nc))
        
        scored_candidates = []
        # Ưu tiên các ô gần cụm HIT nhất
        center_r = sum(r for r, _ in self.hits) / len(self.hits)
        center_c = sum(c for _, c in self.hits) / len(self.hits)

        for r, c in candidates:
            if self._in_bounds(r, c) and ((r,c) in self.possible_shots):
                dist = abs(r - center_r) + abs(c - center_c) # Khoảng cách Manhattan
                scored_candidates.append(((r, c), dist))
        
        scored_candidates.sort(key=lambda x: x[1])
        
        for (coord, _) in scored_candidates:
            if coord not in self.target_queue: 
                self.target_queue.append(coord)

    def _reseed_target_queue(self, tracking_board):
        """
        Tái tạo lại hàng đợi target từ các điểm HIT hiện có.
        """
        self.target_queue.clear()
        self._grow_target_queue_from_hits()
        self._prune_target_queue(tracking_board)