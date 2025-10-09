# FILE: ai_hybrid.py
# IQ 200+: Chiến thuật kết hợp Hunt (xác suất + parity + bonus gần HIT) và Target (suy luận hướng + mở rộng hai đầu)
# Phiên bản này được thiết kế để rất khó đánh bại.

import random
from collections import deque, defaultdict
from logic_game import CellState

class HybridAI:
    def __init__(self, board_size=10, ships_config=None, seed=None):
        self.board_size = board_size
        if seed is not None:
            random.seed(seed)

        # Tập hợp các ô chưa bắn (để truy cập nhanh O(1))
        self.possible_shots = {(r, c) for r in range(board_size) for c in range(board_size)}
        
        # Bảng xếp hạng tie-break để đảm bảo hành vi nhất quán/có thể tái tạo khi nhiều ô có cùng điểm số
        self._tie_break = [(r, c) for r in range(board_size) for c in range(board_size)]
        random.shuffle(self._tie_break) # Xáo trộn một lần khi khởi tạo
        self._tie_rank = {pos: i for i, pos in enumerate(self._tie_break)} # Rank của mỗi vị trí

        # Trạng thái AI
        self.mode = 'hunt'              # Chế độ hiện tại: 'hunt' hoặc 'target'
        self.target_queue = deque()     # Hàng đợi các ô cần bắn khi ở chế độ 'target'
        self.hits = []                  # Danh sách các ô đã trúng của con tàu hiện đang bị tấn công
        self.last_oriented = None       # Hướng được suy luận của tàu đang bị tấn công ('h' hoặc 'v')

    # --------- API chính cho GameState ----------
    def get_move(self, tracking_board, remaining_ships):
        """
        Chọn nước đi tiếp theo. Ưu tiên chế độ target, sau đó là hunt.
        """
        # 1. Luôn thử chế độ TARGET trước nếu có mục tiêu hợp lệ
        self._prune_target_queue(tracking_board) # Loại bỏ các mục tiêu đã bị bắn/không hợp lệ
        while self.target_queue:
            m = self.target_queue.popleft()
            if m in self.possible_shots: # Đảm bảo chưa bắn ô này
                self.possible_shots.remove(m)
                return m

        # 2. Nếu không có mục tiêu hợp lệ trong hàng đợi nhưng vẫn còn 'hits',
        # nghĩa là hàng đợi đã bị cạn hoặc mục tiêu cũ không còn hợp lệ.
        # Cần tái tạo lại hàng đợi target hoặc chuyển về hunt.
        if self.hits and not self.target_queue:
            self.mode = 'target' # Vẫn ưu tiên target, thử tái tạo queue
            self._reseed_target_queue(tracking_board)
            self._prune_target_queue(tracking_board) # Prune lại sau khi reseed
            while self.target_queue:
                m = self.target_queue.popleft()
                if m in self.possible_shots:
                    self.possible_shots.remove(m)
                    return m
            
            # Nếu sau khi reseed mà hàng đợi vẫn rỗng (ví dụ: tất cả các ô xung quanh đều đã bị bắn)
            # thì reset trạng thái target và quay về hunt.
            self.mode = 'hunt'
            self.hits.clear()
            self.last_oriented = None

        # 3. Chế độ HUNT: Tính toán bản đồ xác suất và chọn ô tốt nhất
        self.mode = 'hunt' # Chắc chắn đang ở hunt mode
        scores = self._compute_probability_grid(tracking_board, remaining_ships)
        
        best_move, best_score, best_rank = None, -1.0, (float('inf'), float('inf')) # Rank: (parity_penalty, tie_break_rank)
        
        # Xác định parity tốt nhất để săn (dựa trên độ dài tàu còn lại)
        best_parity = self._get_best_parity_for_hunt(remaining_ships)
        
        # Tính toán bonus cho các ô gần với điểm HIT chưa chìm (nếu có)
        near_hit_bonus = self._get_near_hit_bonus_map(tracking_board)

        # Duyệt qua các ô chưa bắn để tìm nước đi tốt nhất
        for r, c in list(self.possible_shots): # Dùng list() để có thể remove trong vòng lặp nếu cần, nhưng ở đây không cần
            sc = scores[r][c]
            if sc <= 0: continue # Bỏ qua các ô không có khả năng chứa tàu
            
            # Áp dụng bonus gần HIT
            sc += near_hit_bonus[(r, c)]
            
            # Áp dụng parity bias: ưu tiên ô cùng parity, hạ điểm nhẹ ô khác parity
            parity_penalty = 0 
            if ((r + c) % 2) != best_parity:
                sc *= 0.9 # Giảm điểm 10% nếu không đúng parity
                parity_penalty = 1 # Để dùng trong tie-breaking
            
            # Tie-breaking: ưu tiên điểm cao hơn, sau đó là parity, sau đó là rank ngẫu nhiên
            current_rank = (parity_penalty, self._tie_rank[(r, c)])
            
            if sc > best_score or (sc == best_score and current_rank < best_rank):
                best_move, best_score, best_rank = (r, c), sc, current_rank

        # Fallback nếu không tìm thấy nước đi nào có điểm (rất hiếm nếu possible_shots không rỗng)
        if best_move is None:
            if not self.possible_shots:
                return None # Không còn ô nào để bắn
            # Lấy ô đầu tiên trong danh sách đã xáo trộn làm fallback
            best_move = self.possible_shots.pop() 
        else:
            self.possible_shots.remove(best_move)
            
        return best_move

    def report_result(self, move, result):
        """
        AI nhận phản hồi từ game để cập nhật trạng thái và chiến thuật.
        """
        # Chuẩn hóa kết quả
        if isinstance(result, str): res_str = result.strip().lower()
        elif isinstance(result, bool): res_str = 'hit' if result else 'miss'
        else: res_str = str(result).strip().lower()

        if res_str == 'hit':
            self.mode = 'target'
            self.hits.append(move)
            # Sau khi có thêm hit, cố gắng suy luận hướng và mở rộng hàng đợi
            self._refine_orientation() # Cập nhật hướng nếu có thể
            self._grow_target_queue_from_hits() # Mở rộng hàng đợi dựa trên các hits
        elif res_str == 'sunk':
            # Tàu chìm, reset trạng thái target và quay về hunt
            self.mode = 'hunt'
            self.target_queue.clear()
            self.hits.clear()
            self.last_oriented = None
        else:  # miss / already_shot / invalid
            # Nếu bắn trượt trong chế độ target, hàng đợi sẽ tự động bị prune ở lượt tiếp theo.
            pass

    # --------- Logic chế độ TARGET (diệt tàu) ----------
    def _neighbors4(self, r, c):
        """Trả về các ô láng giềng 4 chiều."""
        yield r-1, c; yield r+1, c; yield r, c-1; yield r, c+1

    def _in_bounds(self, r, c):
        """Kiểm tra ô có nằm trong giới hạn bản đồ không."""
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _prune_target_queue(self, tracking_board):
        """
        Loại bỏ các mục tiêu không còn hợp lệ khỏi hàng đợi.
        (Đã bị bắn, nằm ngoài biên, hoặc đã là HIT/MISS).
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
        
        # Sắp xếp các điểm trúng để dễ dàng xác định hướng
        sorted_hits = sorted(self.hits) 
        r0, c0 = sorted_hits[0]
        r1, c1 = sorted_hits[1]

        if r0 == r1: # Cùng hàng -> ngang
            self.last_oriented = 'h'
        elif c0 == c1: # Cùng cột -> dọc
            self.last_oriented = 'v'
        # Nếu chưa xác định được (ví dụ: hits là A1, B2) thì last_oriented vẫn là None,
        # và AI sẽ tiếp tục bắn các ô xung quanh hình chữ thập.

    def _grow_target_queue_from_hits(self):
        """
        Mở rộng hàng đợi mục tiêu dựa trên các điểm HIT hiện có và hướng suy luận.
        """
        if not self.hits: return
        
        # Sắp xếp lại hits để xử lý (đảm bảo thứ tự tăng dần của tọa độ)
        hits_sorted = sorted(self.hits)
        
        candidates = set() # Dùng set để tránh trùng lặp

        if self.last_oriented == 'h': # Đã xác định là ngang
            row = hits_sorted[0][0]
            min_col = min(h[1] for h in hits_sorted)
            max_col = max(h[1] for h in hits_sorted)
            candidates.add((row, min_col - 1)) # Ô bên trái ngoài cùng
            candidates.add((row, max_col + 1)) # Ô bên phải ngoài cùng
        elif self.last_oriented == 'v': # Đã xác định là dọc
            col = hits_sorted[0][1]
            min_row = min(h[0] for h in hits_sorted)
            max_row = max(h[0] for h in hits_sorted)
            candidates.add((min_row - 1, col)) # Ô phía trên ngoài cùng
            candidates.add((max_row + 1, col)) # Ô phía dưới ngoài cùng
        else: # Chưa xác định được hướng (chỉ có 1 HIT hoặc HIT chéo)
            for r, c in hits_sorted:
                for nr, nc in self._neighbors4(r, c):
                    candidates.add((nr, nc))
        
        # Thêm các mục tiêu hợp lệ vào hàng đợi, ưu tiên các ô gần nhất với cụm HIT
        scored_candidates = []
        center_r = sum(r for r, _ in self.hits) / len(self.hits)
        center_c = sum(c for _, c in self.hits) / len(self.hits)

        for r, c in candidates:
            if self._in_bounds(r, c) and ((r,c) in self.possible_shots):
                # Tính khoảng cách Manhattan đến tâm của cụm HIT
                dist = abs(r - center_r) + abs(c - center_c)
                scored_candidates.append(((r, c), dist))
        
        # Sắp xếp để bắn các ô gần cụm HIT nhất trước
        scored_candidates.sort(key=lambda x: x[1])
        
        # Thêm vào target_queue nếu chưa có
        for (coord, _) in scored_candidates:
            if coord not in self.target_queue: # Đảm bảo không thêm trùng lặp
                self.target_queue.append(coord)

    def _reseed_target_queue(self, tracking_board):
        """
        Tái tạo lại hàng đợi target từ các điểm HIT hiện có.
        Hữu ích khi hàng đợi cũ bị cạn hoặc không còn hợp lệ.
        """
        self.target_queue.clear()
        self._grow_target_queue_from_hits()
        self._prune_target_queue(tracking_board)

    # --------- Logic chế độ HUNT (săn tìm) ----------
    def _compute_probability_grid(self, tracking_board, remaining_ships):
        """
        Tính toán bản đồ xác suất cho mỗi ô.
        Giá trị càng cao nghĩa là ô đó có nhiều khả năng chứa một con tàu chưa chìm.
        """
        n = self.board_size
        scores = [[0.0] * n for _ in range(n)]
        
        if not remaining_ships: 
            return scores # Không còn tàu để săn
        
        # Lọc ra độ dài các tàu chưa bị chìm
        ship_lengths = [s.size for s in remaining_ships if not getattr(s, "is_sunk", False)]
        if not ship_lengths:
            return scores

        # Hàm kiểm tra liệu một đoạn tàu có thể đặt được không
        def can_place_segment(segment_coords, exclude_hits=False):
            """
            Kiểm tra xem một đoạn có thể chứa một phần của tàu không.
            Nếu exclude_hits=True, đoạn đó không được chứa bất kỳ ô HIT nào.
            """
            for r, c in segment_coords:
                if not self._in_bounds(r, c): return False
                current_state = tracking_board.grid[r][c]
                if current_state == CellState.MISS or current_state == CellState.SUNK_SHIP:
                    return False
                if exclude_hits and current_state == CellState.HIT: # Dùng cho việc đếm khả năng mới
                    return False
            return True

        # Đếm số cách mỗi ô có thể chứa một con tàu (phương pháp "count-based" probability)
        # Bằng cách này, các ô ở giữa hoặc các ô có thể bắt đầu nhiều đoạn tàu sẽ có điểm cao hơn
        for L in ship_lengths:
            for r in range(n):
                for c in range(n):
                    # Đặt ngang
                    if c + L <= n:
                        segment = [(r, c + i) for i in range(L)]
                        if can_place_segment(segment):
                            for sr, sc in segment:
                                if tracking_board.grid[sr][sc] == CellState.EMPTY:
                                    scores[sr][sc] += 1.0 # Đếm số cách đặt qua ô này
                    # Đặt dọc
                    if r + L <= n:
                        segment = [(r + i, c) for i in range(L)]
                        if can_place_segment(segment):
                            for sr, sc in segment:
                                if tracking_board.grid[sr][sc] == CellState.EMPTY:
                                    scores[sr][sc] += 1.0

        # Nếu đang có các điểm HIT nhưng chưa chìm, ưu tiên các ô liền kề chúng cao hơn
        # để AI tập trung vào việc xác định và diệt tàu.
        if self.hits:
            for r, c in self.hits:
                for nr, nc in self._neighbors4(r, c):
                    if self._in_bounds(nr, nc) and tracking_board.grid[nr][nc] == CellState.EMPTY:
                        scores[nr][nc] += 5.0 # Tăng điểm đáng kể
        
        return scores

    def _get_best_parity_for_hunt(self, remaining_ships):
        """
        Xác định parity tốt nhất để săn (0 hoặc 1) dựa trên độ dài tàu còn lại.
        Nếu còn tàu có độ dài lẻ, sẽ ưu tiên parity đó.
        Nếu tất cả tàu đều có độ dài chẵn, cả hai parity đều như nhau, hoặc có thể ưu tiên một cái cụ thể.
        """
        lengths = [s.size for s in remaining_ships if not getattr(s, "is_sunk", False)]
        
        # Nếu còn tàu có độ dài 1 (Submarine trong cấu hình mặc định là 3, Destroyer là 2)
        # thì parity không còn hiệu quả lắm.
        if 1 in lengths:
            return -1 # Tắt parity
        
        # Nếu còn tàu có độ dài lẻ, ưu tiên parity mà các tàu lẻ này có thể che phủ tốt nhất
        # (Ví dụ: một tàu dài 3 sẽ luôn chiếm 2 ô chẵn và 1 ô lẻ, hoặc ngược lại)
        # Chiến lược phổ biến là ưu tiên các ô xen kẽ (ví dụ: (r+c)%2 == 0) để bao phủ diện tích.
        
        # Đơn giản nhất: nếu còn tàu có độ dài lẻ, nó sẽ ưu tiên một parity nào đó.
        # Ở đây, ta sẽ chọn parity 0 (tức là (r+c) là số chẵn) làm ưu tiên mặc định cho parity hunt.
        # Điều này giúp bao phủ bàn cờ theo kiểu bàn cờ vua.
        return 0 

    def _get_near_hit_bonus_map(self, tracking_board):
        """
        Tính toán bản đồ bonus cho các ô gần với điểm HIT chưa chìm.
        """
        bonus = defaultdict(float) # Default to 0.0
        n = self.board_size
        
        # Chỉ áp dụng bonus nếu đang ở hunt mode và có hits nhưng chưa chìm
        if self.mode == 'hunt' and self.hits: 
            for r, c in self.hits:
                # Tăng bonus cho các ô láng giềng trống xung quanh điểm HIT
                for nr, nc in self._neighbors4(r, c):
                    if self._in_bounds(nr, nc) and tracking_board.grid[nr][nc] == CellState.EMPTY:
                        bonus[(nr, nc)] += 0.5 # Bonus nhẹ hơn so với khi ở target mode
        return bonus