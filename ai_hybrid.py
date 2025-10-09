# FILE: ai_hybrid.py
# IQ 200+++: Chiến thuật kết hợp Hunt (xác suất + parity + bonus gần HIT) và Target (suy luận hướng + mở rộng hai đầu)
# Phiên bản này được thiết kế để CỰC KỲ KHÓ ĐÁNH BẠI, ưu tiên hoàn thành tàu đang tấn công.
# Cải tiến: Quản lý "cụm HIT" và Tối ưu hóa Target Mode dựa trên remaining_ships để tránh lãng phí nước đi.

import random
from collections import deque, defaultdict
from logic_game import CellState

# Cấu trúc để lưu trữ thông tin về một cụm HIT (một con tàu đang bị tấn công)
class ActiveTarget:
    def __init__(self, initial_hit):
        self.hits_in_cluster = [initial_hit] # Các ô đã trúng của cụm này
        self.orientation = None                # Hướng suy luận ('h', 'v', hoặc None)
        self.target_queue = deque()            # Hàng đợi các ô cần bắn để hoàn thành tàu này
        self.min_possible_length = 1           # Độ dài tối thiểu có thể của tàu này (khởi tạo 1)
        self.max_possible_length = 5           # Độ dài tối đa có thể của tàu này (khởi tạo 5 - Carrier)

    def __repr__(self):
        return f"Target(Hits={self.hits_in_cluster}, Ori={self.orientation}, QSize={len(self.target_queue)}, LenRange=[{self.min_possible_length}-{self.max_possible_length}])"

class HybridAI:
    def __init__(self, board_size=10, ships_config=None, seed=None):
        self.board_size = board_size
        if seed is not None:
            random.seed(seed)

        self.possible_shots = {(r, c) for r in range(board_size) for c in range(board_size)}
        self._tie_break = [(r, c) for r in range(board_size) for c in range(board_size)]
        random.shuffle(self._tie_break) 
        self._tie_rank = {pos: i for i, pos in enumerate(self._tie_break)} 

        self.mode = 'hunt'              
        self.active_targets = []        # Danh sách các đối tượng ActiveTarget
        self.last_shot_move = None      

    # --------- API chính cho GameState ----------
    def get_move(self, tracking_board, remaining_ships):
        """
        Chọn nước đi tiếp theo. Ưu tiên chế độ target (hoàn thành các tàu đang tấn công), sau đó là hunt.
        """
        # 1. Ưu tiên hoàn thành các tàu đang bị tấn công (Active Targets)
        self._sort_active_targets() 

        for target in list(self.active_targets): # Iterate over a copy because list might change
            # Luôn cập nhật thông tin cụm trước khi lấy nước đi, bao gồm cả remaining_ships
            self._refine_target_info(target, tracking_board, remaining_ships) 
            self._prune_target_queue_for_cluster(target, tracking_board) 

            while target.target_queue:
                m = target.target_queue.popleft()
                if m in self.possible_shots:
                    self.possible_shots.remove(m)
                    self.last_shot_move = m
                    self.mode = 'target' 
                    return m
            
        # 2. Chế độ HUNT: Nếu không có ActiveTarget nào cung cấp nước đi hợp lệ
        self.mode = 'hunt'
        scores = self._compute_probability_grid(tracking_board, remaining_ships)
        
        best_move, best_score, best_rank = None, -1.0, (float('inf'), float('inf')) 
        
        best_parity = self._get_best_parity_for_hunt(remaining_ships)
        
        for r, c in list(self.possible_shots):
            sc = scores[r][c]
            if sc <= 0: continue 
            
            # Loại trừ các ô đã thuộc active_targets khỏi việc tính toán scores của hunt mode
            is_part_of_active_target = False
            for target in self.active_targets:
                if (r,c) in target.hits_in_cluster:
                    is_part_of_active_target = True
                    break
            if is_part_of_active_target:
                continue 

            parity_penalty = 0 
            if ((r + c) % 2) != best_parity and best_parity != -1: 
                sc *= 0.9 
                parity_penalty = 1 
            
            current_rank = (parity_penalty, self._tie_rank[(r, c)])
            
            if sc > best_score or (sc == best_score and current_rank < best_rank):
                best_move, best_score, best_rank = (r, c), sc, current_rank

        if best_move is None:
            if not self.possible_shots:
                return None 
            move = random.choice(list(self.possible_shots))
            self.possible_shots.remove(move)
            self.last_shot_move = move
            return move
        else:
            self.possible_shots.remove(best_move)
            self.last_shot_move = best_move
            return best_move

    def report_result(self, move, result, sunk_ship_obj=None):
        """
        AI nhận phản hồi từ game để cập nhật trạng thái và chiến thuật.
        Bây giờ có thể nhận sunk_ship_obj để biết tàu nào đã chìm.
        """
        if isinstance(result, str): res_str = result.strip().lower()
        elif isinstance(result, bool): res_str = 'hit' if result else 'miss'
        else: res_str = str(result).strip().lower()

        if res_str == 'hit':
            self.mode = 'target'
            self._update_active_targets_with_hit(move)
            
        elif res_str == 'sunk':
            self.mode = 'hunt'
            self._cleanup_active_targets_after_sunk(sunk_ship_obj)

        else:  # miss / already_shot / invalid
            pass

    # --------- Logic quản lý ActiveTargets ----------
    def _neighbors4(self, r, c):
        yield r-1, c; yield r+1, c; yield r, c-1; yield r, c+1

    def _in_bounds(self, r, c):
        return 0 <= r < self.board_size and 0 <= c < self.board_size

    def _update_active_targets_with_hit(self, new_hit):
        """
        Thêm điểm HIT mới vào cụm đang hoạt động hoặc tạo cụm mới.
        """
        connected_targets = []
        for target in self.active_targets:
            for hit_coord in target.hits_in_cluster:
                if abs(new_hit[0] - hit_coord[0]) + abs(new_hit[1] - hit_coord[1]) == 1: 
                    connected_targets.append(target)
                    break
        
        if not connected_targets:
            new_target = ActiveTarget(new_hit)
            self.active_targets.append(new_target)
            # self._refine_target_info(new_target) # Refined info will be called in get_move
        else:
            main_target = connected_targets[0]
            if new_hit not in main_target.hits_in_cluster:
                main_target.hits_in_cluster.append(new_hit)
            
            for other_target in connected_targets[1:]:
                main_target.hits_in_cluster.extend(other_target.hits_in_cluster)
                self.active_targets.remove(other_target)
            
            main_target.hits_in_cluster = list(set(main_target.hits_in_cluster))
            # self._refine_target_info(main_target) # Refined info will be called in get_move

    def _refine_target_info(self, target: ActiveTarget, tracking_board, remaining_ships):
        """
        Cập nhật hướng và hàng đợi mục tiêu cho một ActiveTarget cụ thể,
        có tính đến kích thước của các tàu còn lại.
        """
        hits = sorted(target.hits_in_cluster)
        current_len = len(hits)

        # Cập nhật độ dài tàu tiềm năng dựa trên hits
        target.min_possible_length = current_len
        
        # 1. Suy luận hướng
        if current_len >= 2:
            is_horizontal = all(h[0] == hits[0][0] for h in hits)
            is_vertical = all(h[1] == hits[0][1] for h in hits)
            
            if is_horizontal:
                target.orientation = 'h'
            elif is_vertical:
                target.orientation = 'v'
            else:
                target.orientation = None
        else:
            target.orientation = None
        
        # 2. Xây dựng/Tái tạo hàng đợi mục tiêu thông minh hơn
        target.target_queue.clear()
        candidates = set()
        
        # Lấy độ dài tối đa của tàu còn lại có thể phù hợp
        remaining_ship_lengths = sorted([s.size for s in remaining_ships if not getattr(s, "is_sunk", False)], reverse=True)
        # Chỉ xét những tàu có thể dài hơn cụm hits hiện tại
        potential_lengths = [L for L in remaining_ship_lengths if L >= current_len]
        
        if not potential_lengths: # Nếu không còn tàu nào có thể dài như cụm hits, thì cụm này có thể đã đủ dài hoặc lỗi
            # Lúc này, có thể tàu đã chìm nhưng chưa được báo cáo, hoặc là lỗi logic
            # Để an toàn, chúng ta sẽ không thêm mục tiêu nào vào hàng đợi của cụm này
            return

        target.max_possible_length = max(potential_lengths)

        if target.orientation == 'h':
            row = hits[0][0]
            min_col = min(h[1] for h in hits)
            max_col = max(h[1] for h in hits)
            
            # Thăm dò về phía trái
            for offset in range(1, target.max_possible_length - current_len + 1):
                c = min_col - offset
                if self._in_bounds(row, c) and tracking_board.grid[row][c] == CellState.EMPTY:
                    candidates.add((row, c))
                else: # Nếu gặp MISS/SUNK/ngoài biên, dừng tìm kiếm theo hướng này
                    break

            # Thăm dò về phía phải
            for offset in range(1, target.max_possible_length - current_len + 1):
                c = max_col + offset
                if self._in_bounds(row, c) and tracking_board.grid[row][c] == CellState.EMPTY:
                    candidates.add((row, c))
                else: # Nếu gặp MISS/SUNK/ngoài biên, dừng tìm kiếm theo hướng này
                    break

        elif target.orientation == 'v':
            col = hits[0][1]
            min_row = min(h[0] for h in hits)
            max_row = max(h[0] for h in hits)

            # Thăm dò về phía trên
            for offset in range(1, target.max_possible_length - current_len + 1):
                r = min_row - offset
                if self._in_bounds(r, col) and tracking_board.grid[r][col] == CellState.EMPTY:
                    candidates.add((r, col))
                else: # Dừng tìm kiếm theo hướng này
                    break

            # Thăm dò về phía dưới
            for offset in range(1, target.max_possible_length - current_len + 1):
                r = max_row + offset
                if self._in_bounds(r, col) and tracking_board.grid[r][col] == CellState.EMPTY:
                    candidates.add((r, col))
                else: # Dừng tìm kiếm theo hướng này
                    break
        else: # Chưa xác định hướng (chỉ 1 hit), bắn xung quanh tất cả các hits trong cụm
            for r, c in hits:
                for nr, nc in self._neighbors4(r, c):
                    if self._in_bounds(nr, nc) and tracking_board.grid[nr][nc] == CellState.EMPTY:
                        candidates.add((nr, nc))
        
        # Ưu tiên các ô gần tâm cụm HIT
        center_r = sum(r for r, _ in hits) / current_len
        center_c = sum(c for _, c in hits) / current_len
        scored_candidates = []
        for r, c in candidates:
            if ((r,c) in self.possible_shots): # Đảm bảo chưa bắn
                dist = abs(r - center_r) + abs(c - center_c)
                scored_candidates.append(((r, c), dist))
        
        scored_candidates.sort(key=lambda x: x[1])
        for (coord, _) in scored_candidates:
            if coord not in target.target_queue: 
                target.target_queue.append(coord)

    def _prune_target_queue_for_cluster(self, target: ActiveTarget, tracking_board):
        """
        Loại bỏ các mục tiêu không còn hợp lệ khỏi hàng đợi của một cụm.
        """
        cleaned_queue = deque()
        for r, c in target.target_queue:
            if self._in_bounds(r, c) and tracking_board.grid[r][c] == CellState.EMPTY and ((r,c) in self.possible_shots):
                cleaned_queue.append((r, c))
        target.target_queue = cleaned_queue
    
    def _cleanup_active_targets_after_sunk(self, sunk_ship_obj):
        """
        Dọn dẹp lại active_targets sau khi một tàu chìm.
        """
        if sunk_ship_obj is None: return
        sunk_coords = set(sunk_ship_obj.coordinates)

        targets_to_keep = []
        for target in self.active_targets:
            original_hits_count = len(target.hits_in_cluster)
            target.hits_in_cluster = [h for h in target.hits_in_cluster if h not in sunk_coords]
            
            if not target.hits_in_cluster:
                continue
            
            if len(target.hits_in_cluster) < original_hits_count:
                # Nếu hits giảm, cần refine lại thông tin (hướng, queue, độ dài)
                # Tuy nhiên, refine_target_info giờ đây được gọi trong get_move,
                # nên việc này sẽ tự động được xử lý ở lượt tiếp theo.
                pass 
            
            targets_to_keep.append(target)
        
        self.active_targets = targets_to_keep


    def _sort_active_targets(self):
        """
        Sắp xếp active_targets để ưu tiên các cụm có nhiều hits hơn,
        hoặc đã có hướng rõ ràng, hoặc có target_queue lớn hơn.
        """
        def sort_key(target: ActiveTarget):
            orientation_score = 2 if target.orientation else 0 # Orientated targets get higher priority
            hits_count = len(target.hits_in_cluster)
            queue_size = len(target.target_queue) # Having more options is good
            
            # Prioritize: (Has_Orientation, Hits_Count, Queue_Size)
            return (orientation_score, hits_count, queue_size) 
        
        self.active_targets.sort(key=sort_key, reverse=True)


    # --------- Logic chế độ HUNT (săn tìm) ----------
    def _can_place_segment(self, segment_coords, tracking_board):
        """
        Kiểm tra xem một đoạn có thể chứa một phần của tàu không,
        có tính đến các ô MISS/SUNK và các ô HIT hiện tại (không thuộc ActiveTarget nào).
        """
        for r, c in segment_coords:
            if not self._in_bounds(r, c): return False
            current_state = tracking_board.grid[r][c]
            if current_state == CellState.MISS or current_state == CellState.SUNK_SHIP:
                return False
            
            if current_state == CellState.HIT:
                is_hit_in_active_target = False
                for target in self.active_targets:
                    if (r,c) in target.hits_in_cluster:
                        is_hit_in_active_target = True
                        break
                if not is_hit_in_active_target:
                    return False 
        return True

    def _compute_probability_grid(self, tracking_board, remaining_ships):
        n = self.board_size
        scores = [[0.0] * n for _ in range(n)]
        
        if not remaining_ships: 
            return scores 
        
        ship_lengths = [s.size for s in remaining_ships if not getattr(s, "is_sunk", False)]
        if not ship_lengths:
            return scores

        for L in ship_lengths:
            # Horizontal placements
            for r in range(n):
                for c in range(n - L + 1):
                    segment = [(r, c + i) for i in range(L)]
                    if self._can_place_segment(segment, tracking_board): 
                        for sr, sc in segment:
                            if tracking_board.grid[sr][sc] == CellState.EMPTY: 
                                scores[sr][sc] += 1.0 
            # Vertical placements
            for c in range(n):
                for r in range(n - L + 1):
                    segment = [(r + i, c) for i in range(L)]
                    if self._can_place_segment(segment, tracking_board): 
                        for sr, sc in segment:
                            if tracking_board.grid[sr][sc] == CellState.EMPTY: 
                                scores[sr][sc] += 1.0
        
        return scores

    def _get_best_parity_for_hunt(self, remaining_ships):
        lengths = [s.size for s in remaining_ships if not getattr(s, "is_sunk", False)]
        
        if 1 in lengths: 
            return -1 
        
        return 0