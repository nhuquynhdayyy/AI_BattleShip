# FILE: gui_game.py
# PHIÊN BẢN HOÀN CHỈNH - TÍCH HỢP ÂM THANH VÀ ĐỒ HỌA NÂNG CAO (V7 - Cải thiện thẩm mỹ & màu sắc)

import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import os 

# *** THÊM IMPORT PYGAME ***
import pygame

from logic_game import GameState, CellState, Ship, Board, FLEET_CONFIG
from ai_blind import BlindAI
from ai_heuristic import HeuristicAI
from ai_hybrid import HybridAI

N = 10
CELL_SIZE = 40 

# --- Global constants for asset paths ---
ASSET_DIR = "assets"
IMAGE_DIR = os.path.join(ASSET_DIR, "images")
ICON_DIR = os.path.join(ASSET_DIR, "icons")
SHIP_IMG_DIR = os.path.join(ASSET_DIR, "ships")

# --- Updated COLORS and FONTS (More vibrant and contrasting) ---
COLORS = {
    "background_dark": "#1A222B", # Rất tối, làm nền chính
    "water_base": "#2C5282",    # Xanh biển đậm, nhưng tươi hơn
    "water_light": "#4299E1",   # Xanh sáng cho một số hiệu ứng
    
    "ship_deck_base": "#A0AEC0",  # Xám bạc cho tàu chưa đặt
    "ship_deck_placed": "#718096",# Xám đậm hơn cho tàu đã đặt trong shipyard
    "ship_gun_base": "#4A5568",   # Xám than cho chi tiết súng
    
    "hit_base": "#FC8181",      # Đỏ hồng sáng cho hit
    "miss_base": "#63B3ED",     # Xanh da trời sáng cho miss
    "sunk_base": "#2D3748",     # Xám xanh rất đậm cho sunk background
    
    "preview_ok": "#68D391",    # Xanh lá cây tươi sáng
    "preview_err": "#F6AD55",   # Cam vàng tươi sáng
    
    "border_grid": "#4A5568",   # Xám đậm cho lưới
    "text_light": "#E2E8F0",    # Gần trắng cho chữ sáng
    "text_dark": "#1A222B",     # Rất tối cho chữ tối
    
    "button_normal": "#4A5568", # Nút màu xám xanh
    "button_hover": "#63B3ED",  # Nút sáng xanh khi hover
    "button_active": "#2D3748", # Nền cho status/ai_strategy
    "selection_highlight": "#FFD700", # Vàng kim nổi bật
    "shipyard_bg": "#2A4365",   # Xanh đậm cho khung shipyard
    "title_bg": "#1A202C",      # Đen đậm cho nền tiêu đề
    "main_title_fg": "#FBD38D", # Vàng cam cho tiêu đề chính (ví dụ: Bảng của bạn)
}

# Fonts (Using Arial for wider compatibility)
FONTS = {
    "title": ("Arial Black", 36, "bold"),
    "subtitle": ("Arial", 20, "bold", "underline"), # Tăng kích thước, nhấn mạnh
    "button": ("Arial", 14, "bold"),
    "label": ("Arial", 11, "bold"), # Tăng kích thước và làm đậm cho nhãn tàu
    "status": ("Arial", 13, "bold") # Tăng kích thước cho status
}

class BattleshipGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("⚓ Battleship - Canvas Edition")
        self.root.withdraw()
        
        # --- CÁC BIẾN TRẠNG THÁI ---
        self.game, self.ai = None, None
        self.selected_ship, self.placement_orientation = None, "horizontal"
        self.shipyard_widgets, self.preview_coords = {}, []
        
        # *** KHỞI TẠO HỆ THỐNG ÂM THANH VÀ TẢI TÀI NGUYÊN ĐỒ HỌA ***
        self._load_assets() 
        
        self.show_difficulty_selection()
        
    def _load_assets(self):
        """Tải tất cả các file âm thanh và hình ảnh vào bộ nhớ."""
        self.images = {}
        self.assets_loaded = False 
        try:
            # --- Load Sounds ---
            pygame.mixer.init()
            self.sounds = {
                'click': pygame.mixer.Sound(os.path.join(ASSET_DIR, "click.wav")),
                'shot': pygame.mixer.Sound(os.path.join(ASSET_DIR, "shot.wav")),
                'hit': pygame.mixer.Sound(os.path.join(ASSET_DIR, "hit.wav")),
                'miss': pygame.mixer.Sound(os.path.join(ASSET_DIR, "miss.wav")),
                'sunk': pygame.mixer.Sound(os.path.join(ASSET_DIR, "sunk.wav")),
                'win': pygame.mixer.Sound(os.path.join(ASSET_DIR, "win.wav")),
                'lose': pygame.mixer.Sound(os.path.join(ASSET_DIR, "lose.wav"))
            }
            pygame.mixer.music.load(os.path.join(ASSET_DIR, "background_music.mp3"))
            pygame.mixer.music.play(loops=-1)
            pygame.mixer.music.set_volume(0.3)
        except pygame.error as e:
            print(f"Cảnh báo: Không thể tải file âm thanh. Game sẽ không có tiếng. Lỗi: {e}")
            self.sounds = None
        
        try:
            # --- Load Images ---
            self.images['bg_difficulty'] = ImageTk.PhotoImage(Image.open(os.path.join(IMAGE_DIR, "background_difficulty.png")).resize((800, 600), Image.LANCZOS))
            
            # Board elements
            self.images['water_tile'] = ImageTk.PhotoImage(Image.open(os.path.join(ICON_DIR, "water_tile.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS))
            self.images['hit_marker'] = ImageTk.PhotoImage(Image.open(os.path.join(ICON_DIR, "hit_marker.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS))
            self.images['miss_marker'] = ImageTk.PhotoImage(Image.open(os.path.join(ICON_DIR, "miss_marker.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS))
            self.images['sunk_marker'] = ImageTk.PhotoImage(Image.open(os.path.join(ICON_DIR, "sunk_marker.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS))

            # Ship segments
            self.ship_segment_images = {
                'deck_h': ImageTk.PhotoImage(Image.open(os.path.join(SHIP_IMG_DIR, "ship_deck_h.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
                'deck_v': ImageTk.PhotoImage(Image.open(os.path.join(SHIP_IMG_DIR, "ship_deck_v.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
                'gun_h': ImageTk.PhotoImage(Image.open(os.path.join(SHIP_IMG_DIR, "ship_gun_h.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)), 
                'gun_v': ImageTk.PhotoImage(Image.open(os.path.join(SHIP_IMG_DIR, "ship_gun_v.png")).resize((CELL_SIZE, CELL_SIZE), Image.LANCZOS)),
            }
            
            print("Đã tải tài nguyên đồ họa thành công.")
            self.assets_loaded = True
        except FileNotFoundError as e:
            print(f"Cảnh báo: Không thể tải một số file hình ảnh. Đảm bảo thư mục '{ASSET_DIR}' và các file cần thiết tồn tại. Lỗi: {e}")
            self.assets_loaded = False
            print("Sử dụng màu sắc mặc định thay thế.")


    def play_sound(self, name):
        """Hàm tiện ích để phát một hiệu ứng âm thanh."""
        if self.sounds and name in self.sounds:
            self.sounds[name].play()
        
    def show_difficulty_selection(self):
        self.difficulty_window = tk.Toplevel(self.root)
        self.difficulty_window.title("Chọn Độ Khó")
        self.difficulty_window.geometry("800x600")
        self.difficulty_window.resizable(False, False)

        if self.assets_loaded and 'bg_difficulty' in self.images:
            bg_label = tk.Label(self.difficulty_window, image=self.images['bg_difficulty'])
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.difficulty_window.configure(bg=COLORS["background_dark"]) 

        title_frame = tk.Frame(self.difficulty_window, bg=COLORS["title_bg"], bd=0) 
        title_frame.pack(pady=(80, 40))
        title_label = tk.Label(title_frame, text="CHỌN ĐỘ KHÓ", font=FONTS["title"], fg=COLORS["main_title_fg"], bg=COLORS["title_bg"], padx=20, pady=5) # Màu tiêu đề chính
        title_label.pack()

        btn_font = FONTS["button"]
        btn_width = 20
        btn_bg_normal = COLORS["button_normal"]
        btn_fg_normal = COLORS["text_light"]
        btn_bg_hover = COLORS["button_hover"]

        def on_enter_btn(e): e.widget['background'] = btn_bg_hover
        def on_leave_btn(e): e.widget['background'] = btn_bg_normal 

        def select_difficulty(level):
            self.play_sound('click')
            self.start_setup(level)

        easy_btn = tk.Button(self.difficulty_window, text="DỄ", font=btn_font, width=btn_width,
                             bg=btn_bg_normal, fg=btn_fg_normal, relief="flat", command=lambda: select_difficulty("1"))
        easy_btn.pack(pady=15)
        easy_btn.bind("<Enter>", on_enter_btn)
        easy_btn.bind("<Leave>", on_leave_btn)

        medium_btn = tk.Button(self.difficulty_window, text="TRUNG BÌNH", font=btn_font, width=btn_width,
                               bg=btn_bg_normal, fg=btn_fg_normal, relief="flat", command=lambda: select_difficulty("2"))
        medium_btn.pack(pady=15)
        medium_btn.bind("<Enter>", on_enter_btn)
        medium_btn.bind("<Leave>", on_leave_btn)

        hard_btn = tk.Button(self.difficulty_window, text="KHÓ", font=btn_font, width=btn_width,
                             bg=btn_bg_normal, fg=btn_fg_normal, relief="flat", command=lambda: select_difficulty("3"))
        hard_btn.pack(pady=15)
        hard_btn.bind("<Enter>", on_enter_btn)
        hard_btn.bind("<Leave>", on_leave_btn)
        
        self.difficulty_window.protocol("WM_DELETE_WINDOW", self.root.destroy)

    # --- Helper methods for shipyard label hover effects ---
    def _on_enter_ship_label(self, event, ship):
        if not ship.coordinates and self.selected_ship != ship:
            event.widget['background'] = COLORS["button_hover"]
    
    def _on_leave_ship_label(self, event, ship):
        if not ship.coordinates and self.selected_ship != ship:
            event.widget['background'] = COLORS["ship_deck_base"]
        elif self.selected_ship == ship:
             event.widget['background'] = COLORS["selection_highlight"]
        else: # If placed and not selected
             event.widget['background'] = COLORS["ship_deck_placed"]
    
    # --- Helper methods for ready button hover effects ---
    def _on_enter_ready_button(self, event):
        if event.widget['state'] == 'normal': 
            event.widget.config(background=COLORS["button_hover"])
    
    def _on_leave_ready_button(self, event):
        if event.widget['state'] == 'normal': 
            event.widget.config(background=COLORS["button_normal"])
        elif event.widget['state'] == 'disabled': # Keep normal bg for disabled
            event.widget.config(background=COLORS["button_normal"])

    def on_board_click(self, r, c):
        self.play_sound('click')
        if not self.game or self.game.ai_board is not None: return 

        if self.selected_ship:
            if self.game.player_board.place_ship(self.selected_ship, r, c, self.placement_orientation):
                ship_lbl = self.shipyard_widgets[self.selected_ship.name]
                ship_lbl.config(bg=COLORS["ship_deck_placed"], fg=COLORS["text_dark"], cursor="arrow")
                ship_lbl.unbind("<Button-1>") 
                ship_lbl.unbind("<Enter>") # Also unbind hover effects for placed ships
                ship_lbl.unbind("<Leave>")
                
                self.selected_ship = None
                self.update_boards()
                
                if all(s.coordinates for s in self.game.player_fleet):
                    self.status_label.config(text="Đã đặt xong! Nhấn Ready để bắt đầu.")
                    self.ready_button.config(state="normal", bg=COLORS["button_normal"]) # Set to normal bg first
                    # Rebind hover for active ready button
                    self.ready_button.bind("<Enter>", self._on_enter_ready_button)
                    self.ready_button.bind("<Leave>", self._on_leave_ready_button)
                else: 
                    self.status_label.config(text="Đặt tàu thành công! Chọn tàu tiếp theo.")
            else: 
                messagebox.showerror("Lỗi", "Không thể đặt tàu tại đây. Đảm bảo không chồng chéo hoặc ra ngoài biên.", parent=self.root)
        else: 
            ship_to_edit = self.game.player_board.find_ship_at(r, c)
            if ship_to_edit and not ship_to_edit.is_sunk:
                self.game.player_board.remove_ship(ship_to_edit)
                ship_lbl = self.shipyard_widgets[ship_to_edit.name]
                ship_lbl.config(bg=COLORS["ship_deck_base"], fg=COLORS["text_light"], cursor="hand2")
                ship_lbl.bind("<Button-1>", lambda e, s=ship_to_edit: self.select_ship(s))
                # Rebind hover effects using the new class methods
                ship_lbl.bind("<Enter>", lambda e, s=ship_to_edit: self._on_enter_ship_label(e, s))
                ship_lbl.bind("<Leave>", lambda e, s=ship_to_edit: self._on_leave_ship_label(e, s))


                self.select_ship(ship_to_edit) 
                self.update_boards()
                self.ready_button.config(state="disabled", bg=COLORS["button_normal"])
                self.ready_button.unbind("<Enter>") # Remove hover for disabled button
                self.ready_button.unbind("<Leave>")
                self.status_label.config(text=f"Đang sửa {ship_to_edit.name}. Hãy đặt lại.")

    def select_ship(self, ship):
        self.play_sound('click')
        if self.selected_ship and self.selected_ship.name in self.shipyard_widgets:
            prev_ship_lbl = self.shipyard_widgets[self.selected_ship.name]
            # Reset old selected ship's style only if it's not already placed (to keep the "placed" color)
            if not self.selected_ship.coordinates: 
                prev_ship_lbl.config(relief="flat", bg=COLORS["ship_deck_base"], bd=0)
        
        self.selected_ship = ship
        if ship.name in self.shipyard_widgets:
            self.shipyard_widgets[ship.name].config(relief="solid", bg=COLORS["selection_highlight"], bd=2, highlightbackground=COLORS["text_light"])
        self.status_label.config(text=f"Đang đặt {ship.name}. Chuột phải để xoay.")
    
    def player_shoot(self, r, c):
        if not self.game or self.game.game_over or self.selected_ship or \
           self.game.ai_board is None or self.game.current_turn != "Player" or \
           self.game.player_tracking_board.grid[r][c] in [CellState.HIT, CellState.MISS, CellState.SUNK_SHIP]: 
            self.status_label.config(text="Không thể bắn tại đây lúc này.")
            return
        
        self.play_sound('shot')
        result, ship = self.game.player_shot(r, c)
        
        if result == "Hit": self.play_sound('hit')
        elif result == "Sunk": self.play_sound('sunk')
        elif result == "Miss": self.play_sound('miss')
        
        self.update_boards()
        
        if self.game.game_over: 
            if self.game.winner == "Player":
                self.play_sound('win')
                self.status_label.config(text="🎉 Bạn thắng!"); messagebox.showinfo("Game Over", "Bạn đã thắng!", parent=self.root)
            else: 
                pass 
        elif result == "Sunk":
            self.status_label.config(text=f"Bạn: {ship.name} bị chìm! Bắn tiếp.")
        elif result == "Hit":
            self.status_label.config(text=f"Bạn: Trúng! Bắn tiếp.")
        elif result == "Miss":
            self.status_label.config(text="Bạn: Trượt! Lượt của AI..."); self.root.after(500, self.ai_turn)
        elif result == "Already_Shot": 
            self.status_label.config(text="Ô này đã bắn rồi!")

    def ai_turn(self):
        if not self.game or self.game.game_over: return
        
        self.play_sound('shot')
        result, ship, move = self.game.ai_shot(self.ai)
        
        if result == "Hit": self.play_sound('hit')
        elif result == "Sunk": self.play_sound('sunk')
        elif result == "Miss": self.play_sound('miss')
        
        ai_mode = getattr(self.ai, "mode", "blind").capitalize() 
        if not ai_mode: ai_mode = "N/A" 
        self.ai_strategy_label.config(text=f"AI Strategy: {ai_mode} Mode")
        self.update_boards()
        
        if self.game.game_over: 
            if self.game.winner == "AI":
                self.play_sound('lose')
                self.status_label.config(text=f"🤖 AI thắng!"); messagebox.showinfo("Game Over", "AI đã thắng.", parent=self.root)
            else: 
                pass
        elif result == "Sunk":
            self.play_sound('sunk')
            self.status_label.config(text=f"AI ({ai_mode}): {ship.name} bị chìm! AI bắn tiếp."); self.root.after(500, self.ai_turn)
        elif result == "Hit":
            self.status_label.config(text=f"AI ({ai_mode}): Trúng! AI bắn tiếp."); self.root.after(500, self.ai_turn)
        elif result == "Miss":
            self.status_label.config(text=f"AI ({ai_mode}): Trượt! Lượt của bạn.")
        elif result == "AI_Error" or result == "No_Move":
             self.status_label.config(text=f"AI lỗi hoặc không có nước đi, chuyển lượt.")
             if result == "AI_Error" : self.game.switch_turn() 

    def setup_main_window(self):
        for widget in self.root.winfo_children(): widget.destroy()

        self.root.state('zoomed') 
        self.root.update_idletasks() 

        screen_width = self.root.winfo_width()
        screen_height = self.root.winfo_height()

        if self.assets_loaded:
            try:
                bg_main_pil = Image.open(os.path.join(IMAGE_DIR, "background_main.png"))
                self.images['bg_main'] = ImageTk.PhotoImage(bg_main_pil.resize((screen_width, screen_height), Image.LANCZOS))
            except FileNotFoundError as e:
                print(f"Cảnh báo: Không tải được background_main.png. Lỗi: {e}. Sử dụng màu nền thay thế.")
                self.images['bg_main'] = None

        self.main_bg_canvas = tk.Canvas(self.root, highlightthickness=0)
        self.main_bg_canvas.pack(fill="both", expand=True) 
        
        if self.assets_loaded and self.images.get('bg_main'):
            self.main_bg_canvas.create_image(0, 0, image=self.images['bg_main'], anchor="nw")
        else:
            self.main_bg_canvas.configure(bg=COLORS["background_dark"]) # Fallback to dark background color

        game_content_frame = tk.Frame(self.main_bg_canvas, bg=COLORS["background_dark"], bd=0, relief="flat") # Use dark background for content frame
        self.main_bg_canvas.create_window(screen_width / 2, screen_height / 2, window=game_content_frame, anchor="center")
        
        game_content_frame.grid_rowconfigure(0, weight=1) 
        game_content_frame.grid_columnconfigure((0, 1, 2), weight=1) 

        top_game_area_frame = tk.Frame(game_content_frame, bg=COLORS["background_dark"]) # Use dark background
        top_game_area_frame.grid(row=0, column=0, columnspan=3, pady=10, sticky="nsew") 

        top_game_area_frame.grid_columnconfigure(0, weight=1, minsize=CELL_SIZE * 5) 
        top_game_area_frame.grid_columnconfigure(1, weight=2, minsize=N * CELL_SIZE) 
        top_game_area_frame.grid_columnconfigure(2, weight=2, minsize=N * CELL_SIZE) 
        top_game_area_frame.grid_rowconfigure(0, weight=1) 

        # --- Shipyard Column ---
        shipyard_column = tk.Frame(top_game_area_frame, bg=COLORS["background_dark"]) # Use dark background
        shipyard_column.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.shipyard_outer_frame = tk.Frame(shipyard_column, bg=COLORS["shipyard_bg"], padx=15, pady=15, bd=3, relief="raised") # Increased padding, border, and relief for more depth
        self.shipyard_outer_frame.pack(fill="both", expand=True) 
        tk.Label(self.shipyard_outer_frame, text="XƯỞNG TÀU", font=FONTS["subtitle"], fg=COLORS["main_title_fg"], bg=COLORS["shipyard_bg"]).pack(pady=(0,15)) # Increased pady
        self.shipyard_frame = tk.Frame(self.shipyard_outer_frame, bg=COLORS["shipyard_bg"]) 
        self.shipyard_frame.pack(fill="x") 

        # --- Player Board Column ---
        player_column = tk.Frame(top_game_area_frame, bg=COLORS["background_dark"]) # Use dark background
        player_column.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        player_board_title_frame = tk.Frame(player_column, bg=COLORS["background_dark"]) # Use dark background
        player_board_title_frame.pack(pady=(0, 5))
        tk.Label(player_board_title_frame, text="🧑 BẢNG CỦA BẠN", font=FONTS["subtitle"], fg=COLORS["main_title_fg"], bg=COLORS["background_dark"]).pack() # Main title foreground
        self.player_canvas = self._create_board(player_column, is_player_board=True) 

        # --- AI Board Column ---
        ai_column = tk.Frame(top_game_area_frame, bg=COLORS["background_dark"]) # Use dark background
        ai_column.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)

        ai_board_title_frame = tk.Frame(ai_column, bg=COLORS["background_dark"]) # Use dark background
        ai_board_title_frame.pack(pady=(0, 5))
        tk.Label(ai_board_title_frame, text="🤖 BẢNG ĐỐI THỦ", font=FONTS["subtitle"], fg=COLORS["main_title_fg"], bg=COLORS["background_dark"]).pack() # Main title foreground
        self.ai_canvas = self._create_board(ai_column, is_ai_board=True)

        # --- Bottom Controls Frame (Spanning all columns) ---
        bottom_controls_frame = tk.Frame(game_content_frame, bg=COLORS["background_dark"], bd=0) # Use dark background
        bottom_controls_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew") 

        self.status_label = tk.Label(bottom_controls_frame, text="...", font=FONTS["status"], bg=COLORS["button_active"], fg=COLORS["text_light"], height=2, wraplength=int(screen_width * 0.7)); self.status_label.pack(pady=5, fill="x", padx=20)
        self.ai_strategy_label = tk.Label(bottom_controls_frame, text="AI Strategy: None", font=FONTS["label"], fg=COLORS["text_light"], bg=COLORS["background_dark"]); self.ai_strategy_label.pack(pady=2)

        control_frame = tk.Frame(bottom_controls_frame, bg=COLORS["background_dark"]); control_frame.pack(pady=10) # Use dark background
        
        btn_font = FONTS["button"]
        btn_bg_normal = COLORS["button_normal"]
        btn_fg_normal = COLORS["text_light"]
        btn_bg_hover = COLORS["button_hover"]

        def on_enter_ctrl_btn(e): e.widget['background'] = btn_bg_hover
        def on_leave_ctrl_btn(e): e.widget['background'] = btn_bg_normal

        reset_btn = tk.Button(control_frame, text="🔄 Reset", width=10, command=self.reset_game, 
                              bg=btn_bg_normal, fg=btn_fg_normal, font=btn_font, relief="flat", padx=5, pady=5)
        reset_btn.grid(row=0, column=0, padx=10) # Added padx
        reset_btn.bind("<Enter>", on_enter_ctrl_btn)
        reset_btn.bind("<Leave>", on_leave_ctrl_btn)

        quit_btn = tk.Button(control_frame, text="❌ Quit", width=10, command=self.root.quit, 
                             bg=btn_bg_normal, fg=btn_fg_normal, font=btn_font, relief="flat", padx=5, pady=5)
        quit_btn.grid(row=0, column=1, padx=10) # Added padx
        quit_btn.bind("<Enter>", on_enter_ctrl_btn)
        quit_btn.bind("<Leave>", on_leave_ctrl_btn)
        
        self.root.bind("<Button-3>", self.rotate_ship)
        
        self.root.update_idletasks() 

    def start_setup(self, difficulty):
        self.difficulty_window.destroy()
        self.setup_main_window() 
        self.root.deiconify() 
        
        self.game = GameState()
        if difficulty == "1": self.ai = BlindAI(board_size=N); self.ai_strategy_label.config(text="AI Strategy: Dễ (Mù)")
        elif difficulty == "2": self.ai = HeuristicAI(board_size=N); self.ai_strategy_label.config(text="AI Strategy: Trung bình (Heuristic)")
        elif difficulty == "3": self.ai = HybridAI(board_size=N); self.ai_strategy_label.config(text="AI Strategy: Khó (Hybrid)")
        
        self._initialize_shipyard_widgets() 
        self.status_label.config(text="Click một tàu từ Xưởng Tàu để đặt.")
    
    def reset_game(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.root.withdraw()
        self.show_difficulty_selection()
    
    def _create_board(self, parent, is_player_board=False, is_ai_board=False):
        canvases = []
        board_frame = tk.Frame(parent, bg=COLORS["water_base"], bd=2, relief="sunken") # Added border and relief for board
        board_frame.pack() 

        for r_idx in range(N):
            row_canvases = [] 
            for c_idx in range(N):
                canvas = tk.Canvas(board_frame, width=CELL_SIZE, height=CELL_SIZE, bg=COLORS['water_base'], highlightthickness=1, highlightbackground=COLORS['border_grid'])
                if self.assets_loaded and 'water_tile' in self.images:
                    canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['water_tile'], anchor='center', tags="water")
                else:
                    canvas.create_rectangle(0, 0, CELL_SIZE, CELL_SIZE, fill=COLORS['water_base'], outline=COLORS['border_grid'], tags="water")

                if is_player_board:
                    canvas.bind("<Enter>", lambda e, r=r_idx, c=c_idx: self.on_board_hover(r, c)); 
                    canvas.bind("<Leave>", lambda e: self.clear_preview())
                    canvas.bind("<Button-1>", lambda e, r=r_idx, c=c_idx: self.on_board_click(r, c))
                if is_ai_board: 
                    canvas.bind("<Button-1>", lambda e, r=r_idx, c=c_idx: self.player_shoot(r, c))
                canvas.grid(row=r_idx, column=c_idx)
                row_canvases.append(canvas)
            canvases.append(row_canvases)
        return canvases
    
    def update_boards(self):
        if not self.game: return
        self._draw_board(self.player_canvas, self.game.player_board, show_ships=True)
        if self.game.ai_board: self._draw_board(self.ai_canvas, self.game.player_tracking_board, show_ships=False)
    
    def _draw_board(self, canvases, board, show_ships):
        for r in range(N):
            for c in range(N):
                canvas = canvases[r][c]
                canvas.delete("all") 

                if self.assets_loaded and 'water_tile' in self.images:
                     canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['water_tile'], anchor='center', tags="water")
                else:
                    canvas.create_rectangle(0, 0, CELL_SIZE, CELL_SIZE, fill=COLORS['water_base'], outline=COLORS['border_grid'], tags="water")
                
                cell_state = board.grid[r][c]
                
                if show_ships and cell_state in [CellState.SHIP, CellState.HIT, CellState.SUNK_SHIP]: 
                    ship = board.find_ship_at(r, c)
                    if ship:
                        if not ship.is_sunk: 
                            self._draw_ship_part(canvas, ship, ship.coordinates.index((r, c)))
                        else: 
                            pass 
                
                if cell_state == CellState.MISS:
                    if self.assets_loaded and 'miss_marker' in self.images:
                        canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['miss_marker'], anchor='center')
                    else: 
                        canvas.create_oval(10, 10, CELL_SIZE-10, CELL_SIZE-10, fill=COLORS['miss_base'], outline='white')
                elif cell_state == CellState.HIT:
                    if self.assets_loaded and 'hit_marker' in self.images:
                        canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['hit_marker'], anchor='center')
                    else: 
                        canvas.create_oval(5, 5, CELL_SIZE-5, CELL_SIZE-5, fill=COLORS['hit_base'], outline='orange')
                elif cell_state == CellState.SUNK_SHIP:
                    if self.assets_loaded and 'sunk_marker' in self.images:
                        canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=self.images['sunk_marker'], anchor='center')
                    else: 
                        canvas.create_rectangle(0, 0, CELL_SIZE, CELL_SIZE, fill=COLORS['sunk_base'], outline=COLORS['border_grid'])
                        canvas.create_text(CELL_SIZE/2, CELL_SIZE/2, text="💀", font=("Arial", 15), fill="white")

    def _draw_ship_part(self, canvas, ship, part_index):
        if not self.assets_loaded or not self.ship_segment_images:
            if ship.orientation == 'horizontal':
                canvas.create_rectangle(0, 5, CELL_SIZE, CELL_SIZE-5, fill=COLORS['ship_deck_base'], outline=COLORS['ship_gun_base'])
                if part_index % 2 == 1: canvas.create_rectangle(10, 12, CELL_SIZE-10, CELL_SIZE-12, fill=COLORS['ship_gun_base'])
            else:
                canvas.create_rectangle(5, 0, CELL_SIZE-5, CELL_SIZE, fill=COLORS['ship_deck_base'], outline=COLORS['ship_gun_base'])
                if part_index % 2 == 1: canvas.create_rectangle(12, 10, CELL_SIZE-12, CELL_SIZE-10, fill=COLORS['ship_gun_base'])
            return

        if ship.orientation == 'horizontal':
            deck_img = self.ship_segment_images['deck_h']
            gun_img = self.ship_segment_images['gun_h']
            canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=deck_img, anchor='center', tags="ship_part")
            if part_index % 2 == 1: 
                canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=gun_img, anchor='center', tags="ship_gun")
        else: # Vertical
            deck_img = self.ship_segment_images['deck_v']
            gun_img = self.ship_segment_images['gun_v']
            canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=deck_img, anchor='center', tags="ship_part")
            if part_index % 2 == 1:
                canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=gun_img, anchor='center', tags="ship_gun")

    def _initialize_shipyard_widgets(self):
        for widget in self.shipyard_frame.winfo_children(): 
            widget.destroy()
        self.shipyard_widgets.clear()
        
        def on_enter_ship_lbl(event, ship):
            if not ship.coordinates and self.selected_ship != ship:
                event.widget['background'] = COLORS["button_hover"]
        def on_leave_ship_lbl(event, ship):
            if not ship.coordinates and self.selected_ship != ship:
                event.widget['background'] = COLORS["ship_deck_base"]
            elif self.selected_ship == ship:
                 event.widget['background'] = COLORS["selection_highlight"]
            else: # If placed and not selected
                 event.widget['background'] = COLORS["ship_deck_placed"]

        for ship in self.game.player_fleet:
            ship_text = f"{ship.name} ({ship.size} ô)" 
            lbl = tk.Label(self.shipyard_frame, text=ship_text, fg=COLORS["text_light"], bg=COLORS["ship_deck_base"], 
                           padx=10, pady=8, cursor="hand2", font=FONTS["label"], relief="flat", bd=0)
            lbl.pack(pady=4, fill="x")
            lbl.bind("<Button-1>", lambda e, s=ship: self.select_ship(s))
            lbl.bind("<Enter>", lambda e, s=ship: self._on_enter_ship_label(e, s))
            lbl.bind("<Leave>", lambda e, s=ship: self._on_leave_ship_label(e, s))
            self.shipyard_widgets[ship.name] = lbl
            
            if ship.coordinates:
                lbl.config(bg=COLORS["ship_deck_placed"], fg=COLORS["text_dark"], cursor="arrow")
                lbl.unbind("<Button-1>")
                lbl.unbind("<Enter>")
                lbl.unbind("<Leave>")
            
        self.ready_button = tk.Button(self.shipyard_outer_frame, text="🚀 SẴN SÀNG", width=15, command=self.start_game, 
                                       bg=COLORS["button_normal"], fg=COLORS["text_light"], font=FONTS["button"], 
                                       relief="flat", padx=5, pady=8, state="disabled")
        self.ready_button.pack(pady=15)
        
        self.ready_button.bind("<Enter>", self._on_enter_ready_button)
        self.ready_button.bind("<Leave>", self._on_leave_ready_button)

        if all(s.coordinates for s in self.game.player_fleet):
            self.ready_button.config(state="normal", bg=COLORS["button_normal"]) 
        else:
            self.ready_button.config(state="disabled", bg=COLORS["button_normal"])

    def on_board_hover(self, r, c):
        if not self.selected_ship: return
        self.clear_preview()
        is_placeable = self.game.player_board._is_valid_placement(self.selected_ship.size, r, c, self.placement_orientation)
        color = COLORS["preview_ok"] if is_placeable else COLORS["preview_err"]
        
        preview_segment_img = None
        if self.assets_loaded and self.ship_segment_images:
            if self.placement_orientation == "horizontal":
                preview_segment_img = self.ship_segment_images['deck_h']
            else: 
                preview_segment_img = self.ship_segment_images['deck_v']

        for i in range(self.selected_ship.size):
            row, col = r + (i if self.placement_orientation == "vertical" else 0), c + (i if self.placement_orientation == "horizontal" else 0)
            if 0 <= row < N and 0 <= col < N:
                canvas = self.player_canvas[row][col]
                if preview_segment_img:
                    img_pil = ImageTk.getimage(preview_segment_img) 
                    img_pil_alpha = img_pil.copy()
                    alpha_val = 150 if is_placeable else 90 
                    img_pil_alpha.putalpha(alpha_val) 
                    trans_img = ImageTk.PhotoImage(img_pil_alpha)
                    
                    rect = canvas.create_image(CELL_SIZE/2, CELL_SIZE/2, image=trans_img, anchor='center', tags="preview_ship")
                    self.preview_coords.append((canvas, rect, trans_img)) 
                else: 
                    rect = canvas.create_rectangle(0,0,CELL_SIZE,CELL_SIZE, fill=color, outline=color, stipple="gray50") 
                    self.preview_coords.append((canvas, rect))
    
    def clear_preview(self):
        for item in self.preview_coords:
            canvas = item[0]
            canvas.delete(item[1]) 
        self.preview_coords = []

    def rotate_ship(self, event):
        if not self.selected_ship: return
        self.placement_orientation = "vertical" if self.placement_orientation == "horizontal" else "horizontal"
        
        x, y = event.x_root, event.y_root 
        
        for r_board in range(N):
            for c_board in range(N):
                canvas = self.player_canvas[r_board][c_board]
                canvas_x, canvas_y = canvas.winfo_rootx(), canvas.winfo_rooty()
                
                if (canvas_x <= x < canvas_x + CELL_SIZE) and \
                   (canvas_y <= y < canvas_y + CELL_SIZE):
                    self.on_board_hover(r_board, c_board)
                    return
        self.clear_preview() 

    def start_game(self):
        self.play_sound('click')
        if self.selected_ship and self.selected_ship.name in self.shipyard_widgets:
            prev_ship_lbl = self.shipyard_widgets[self.selected_ship.name]
            if not self.selected_ship.coordinates: 
                prev_ship_lbl.config(relief="flat", bg=COLORS["ship_deck_base"], bd=0)
        self.selected_ship = None
        self.clear_preview()
        
        self.ready_button.config(state="disabled", bg=COLORS["button_normal"])
        self.shipyard_outer_frame.destroy() 
        
        self.game.start_battle() 
        self.update_boards()
        self.status_label.config(text="Trận chiến bắt đầu! Đến lượt bạn bắn!")

if __name__ == "__main__":
    root = tk.Tk()
    app = BattleshipGUI(root)
    root.mainloop()