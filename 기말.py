import random
import re
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import requests


class SoloHangmanGame:

    def __init__(self, root):
        self.root = root
        self.root.title("HANGMAN ARCADE - 온라인 랭킹 에디션")
        self.root.geometry("560x660")
        self.root.resizable(False, False)

        # 온라인 연동 주소 설정
        self.words_url = "https://raw.githubusercontent.com/yujin-76/hangman_txt/refs/heads/main/word.txt"
        self.firebase_base_url = "https://hangman-ranking-default-rtdb.firebaseio.com/rankings"
        self.firebase_url = f"{self.firebase_base_url}.json"

        # 모던 네온 다크 테마 색상표
        self.colors = {
            "bg": "#0F172A",
            "card": "#1E293B",
            "btn_bg": "#334155",
            "btn_fg": "#F8FAFC",
            "neon_blue": "#38BDF8",
            "neon_yellow": "#FACC15",
            "neon_green": "#10B981",
            "neon_red": "#F43F5E",
            "muted": "#94A3B8",
        }
        self.root.configure(bg=self.colors["bg"])

        # 1. GitHub에서 단어장 불러오기
        self.word_pool = self.load_words()

        # 2. 게임 상태 변수
        self.player_nickname = "PLAYER"
        self.secret_word = ""
        self.guessed_letters = set()
        self.wrong_count = 0
        self.max_attempts = 6
        self.score = 0
        self.combo = 0
        self.is_game_over = True

        # 3. UI 위젯 참조 변수
        self.letter_buttons = {}
        self.answer_entry = None
        self.submit_ans_btn = None

        # 4. 전역 키보드 및 마우스 클릭 이벤트 연결
        self.root.bind("<Key>", self.handle_keypress)
        self.root.bind("<Button-1>", self.handle_global_click)

        # 첫 화면(메인 로비) 표시
        self.show_menu_screen()

    # =========================================================================
    # 1. GitHub 온라인 단어장 불러오기
    # =========================================================================
    def load_words(self):
        """GitHub Raw URL에서 최신 영단어 목록을 읽어옵니다."""
        default_words = [
            "PYTHON", "KEYBOARD", "ALGORITHM", "UNIVERSE", "CHAMPION",
            "STRATEGY", "ADVENTURE", "DATABASE", "COMPILER", "SPECTRUM",
            "FUNCTION", "VARIABLE", "NETWORK", "SOFTWARE", "TERMINAL",
        ]

        try:
            response = requests.get(self.words_url, timeout=4)
            if response.status_code == 200:
                loaded_words = []
                for line in response.text.splitlines():
                    word = line.strip().upper()
                    if word.isalpha() and len(word) >= 2:
                        loaded_words.append(word)
                if loaded_words:
                    return loaded_words
        except Exception:
            pass  # 오프라인이거나 접속 지연 시 기본 단어 사용

        return default_words

    # =========================================================================
    # 2. Firebase 온라인 랭킹 관리 (저장 및 조회)
    # =========================================================================
    def save_ranking(self, nickname, score):
        """닉네임별 기존 최고 기록보다 높은 점수일 때만 Firebase DB에 덮어씁니다."""
        if score <= 0:
            return

        # Firebase 경로에 사용할 수 없는 특수문자(. # $ [ ] /) 치환
        safe_key = re.sub(r'[.#$\[\]/]', '_', nickname).strip()
        if not safe_key:
            return

        user_url = f"{self.firebase_base_url}/{safe_key}.json"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        payload = {
            "nickname": nickname,
            "score": score,
            "played_at": now_str,
        }

        try:
            # 1. 해당 닉네임의 기존 기록 조회
            res = requests.get(user_url, timeout=4)
            old_data = res.json() if res.status_code == 200 else None
            old_score = int(old_data.get("score", 0)) if isinstance(old_data, dict) else 0

            # 2. 기존 최고 점수보다 높을 때만 덮어쓰기 (PUT)
            if score > old_score:
                requests.put(user_url, json=payload, timeout=4)
        except Exception:
            messagebox.showwarning(
                "네트워크 오류",
                "인터넷 연결이 원활하지 않아 온라인 랭킹에 점수를 등록하지 못했습니다."
            )

    def get_top_rankings(self, limit=5):
        """Firebase DB에서 전체 기록을 가져와 점수가 높은 순으로 상위 N명을 반환합니다."""
        try:
            response = requests.get(self.firebase_url, timeout=4)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    return []

                records = []
                for key, item in data.items():
                    if isinstance(item, dict) and "score" in item:
                        records.append((
                            item.get("nickname", "UNKNOWN"),
                            int(item.get("score", 0)),
                            item.get("played_at", ""),
                            key,
                        ))

                # 점수 내림차순, 동점일 경우 닉네임 오름차순 정렬
                records.sort(key=lambda x: (-x[1], x[3]))
                return [(r[0], r[1], r[2]) for r in records[:limit]]
        except Exception:
            pass

        return []

    def get_best_score(self):
        """역대 1위 점수를 반환합니다."""
        top = self.get_top_rankings(limit=1)
        return top[0][1] if top else 0

    # =========================================================================
    # 3. 공통 화면 제어 및 입력창 포커스 관리
    # =========================================================================
    def clear_screen(self):
        """화면 전환을 위해 현재 창의 모든 위젯을 비웁니다."""
        for widget in self.root.winfo_children():
            widget.destroy()
        self.letter_buttons.clear()
        self.answer_entry = None
        self.submit_ans_btn = None

    def handle_global_click(self, event):
        """정답 입력창 바깥 영역을 클릭하면 입력창 포커스를 해제합니다."""
        if not isinstance(event.widget, tk.Entry):
            self.root.focus_set()

    def release_entry_focus(self, event=None):
        """Esc 또는 [취소] 버튼 클릭 시 입력창을 비우고 빠져나옵니다."""
        if self.answer_entry:
            self.answer_entry.delete(0, tk.END)
        self.root.focus_set()

    # =========================================================================
    # 4. [화면 1] 메인 로비 (닉네임 입력 · 게임 시작 · 랭킹)
    # =========================================================================
    def show_menu_screen(self):
        self.clear_screen()
        self.is_game_over = True

        tk.Label(
            self.root,
            text="HANGMAN",
            font=("Consolas", 42, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["neon_blue"],
        ).pack(pady=(60, 5))

        tk.Label(
            self.root,
            text="ONLINE ARCADE & RANKING EDITION",
            font=("Consolas", 12, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["muted"],
        ).pack(pady=(0, 35))

        # 메인 시작 카드
        card = tk.Frame(self.root, bg=self.colors["card"], padx=25, pady=24)
        card.pack(fill="x", padx=55)

        tk.Label(
            card,
            text="👤 도전자 닉네임 (최대 12자):",
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors["card"],
            fg=self.colors["neon_yellow"],
        ).pack(anchor="w", pady=(0, 6))

        nick_entry = tk.Entry(
            card,
            font=("맑은 고딕", 12, "bold"),
            bg=self.colors["btn_bg"],
            fg="white",
            insertbackground="white",
            relief="flat",
        )
        nick_entry.pack(fill="x", ipady=5, pady=(0, 18))
        nick_entry.insert(0, self.player_nickname)
        nick_entry.focus_set()

        def on_start():
            nick = nick_entry.get().strip()
            if not nick:
                messagebox.showwarning("입력 확인", "랭킹에 등록할 닉네임을 입력해 주세요!")
                nick_entry.focus_set()
                return
            if len(nick) > 12:
                messagebox.showwarning("입력 확인", "닉네임은 12자 이내로 입력해 주세요!")
                return
            self.player_nickname = nick
            self.start_game_screen()

        tk.Button(
            card,
            text="🕹️ 게임 시작하기",
            font=("맑은 고딕", 13, "bold"),
            bg=self.colors["neon_blue"],
            fg="#0F172A",
            activebackground="#7DD3FC",
            relief="flat",
            pady=10,
            cursor="hand2",
            command=on_start,
        ).pack(fill="x")

        nick_entry.bind("<Return>", lambda e: on_start())

        # 명예의 전당 랭킹 버튼
        tk.Button(
            self.root,
            text=f"🏆 실시간 명예의 전당 TOP 5 (현재 1위: {self.get_best_score():,}점)",
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["btn_bg"],
            fg=self.colors["neon_yellow"],
            activebackground="#475569",
            relief="flat",
            width=38,
            pady=11,
            cursor="hand2",
            command=self.show_ranking_screen,
        ).pack(pady=(24, 10))

        # 등록된 단어 개수 안내 라벨
        tk.Label(
            self.root,
            text=f"📚 온라인 단어장 연동 완료 (총 {len(self.word_pool)}개 단어 수록)",
            font=("맑은 고딕", 9),
            bg=self.colors["bg"],
            fg=self.colors["muted"],
        ).pack(pady=(12, 0))

    # =========================================================================
    # 5. [화면 2] 게임 플레이 화면
    # =========================================================================
    def start_game_screen(self):
        self.clear_screen()
        self.score = 0
        self.combo = 0

        # 상단 내비게이션 바
        nav_bar = tk.Frame(self.root, bg=self.colors["bg"])
        nav_bar.pack(fill="x", padx=20, pady=(12, 5))

        tk.Button(
            nav_bar,
            text="🏠 메인 메뉴",
            font=("맑은 고딕", 9, "bold"),
            bg=self.colors["card"],
            fg="white",
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.exit_to_menu,
        ).pack(side=tk.LEFT)

        tk.Label(
            nav_bar,
            text=f"PLAYER: {self.player_nickname}",
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["neon_blue"],
        ).pack(side=tk.RIGHT)

        # 점수 / 콤보 / 최고기록 전광판
        board = tk.Frame(self.root, bg=self.colors["card"], padx=15, pady=10)
        board.pack(fill="x", padx=20, pady=5)

        self.score_label = tk.Label(
            board, text="SCORE: 0", font=("Consolas", 12, "bold"),
            bg=self.colors["card"], fg=self.colors["neon_green"]
        )
        self.score_label.pack(side=tk.LEFT)

        self.combo_label = tk.Label(
            board, text="0 COMBO", font=("Consolas", 12, "bold"),
            bg=self.colors["card"], fg=self.colors["neon_yellow"]
        )
        self.combo_label.pack(side=tk.LEFT, padx=35)

        self.best_label = tk.Label(
            board, text=f"TOP 1: {self.get_best_score()}", font=("Consolas", 12, "bold"),
            bg=self.colors["card"], fg=self.colors["neon_blue"]
        )
        self.best_label.pack(side=tk.RIGHT)

        # 안내 메시지 및 행맨 캔버스
        self.info_label = tk.Label(
            self.root, text="", font=("맑은 고딕", 11, "bold"),
            bg=self.colors["bg"], fg="white"
        )
        self.info_label.pack(pady=(8, 4))

        self.canvas = tk.Canvas(
            self.root, width=250, height=185,
            bg=self.colors["card"], highlightthickness=0
        )
        self.canvas.pack(pady=6)

        # 단어 빈칸 라벨
        self.word_label = tk.Label(
            self.root, text="", font=("Consolas", 26, "bold"),
            bg=self.colors["bg"], fg="white"
        )
        self.word_label.pack(pady=4)

        # 정답 직접 입력창 영역
        direct_frame = tk.Frame(self.root, bg=self.colors["card"], padx=10, pady=6)
        direct_frame.pack(pady=(2, 8))

        tk.Label(
            direct_frame, text="✍️ 정답 입력:", font=("맑은 고딕", 9, "bold"),
            bg=self.colors["card"], fg=self.colors["neon_yellow"]
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.answer_entry = tk.Entry(
            direct_frame, width=15, font=("Consolas", 12, "bold"),
            bg=self.colors["btn_bg"], fg="white", insertbackground="white", relief="flat"
        )
        self.answer_entry.pack(side=tk.LEFT, padx=(0, 6), ipady=2)
        self.answer_entry.bind("<Return>", lambda e: self.submit_full_word())
        self.answer_entry.bind("<Escape>", self.release_entry_focus)

        self.submit_ans_btn = tk.Button(
            direct_frame, text="제출", font=("맑은 고딕", 9, "bold"),
            bg=self.colors["neon_green"], fg="#0F172A", relief="flat",
            padx=8, pady=2, cursor="hand2", command=self.submit_full_word
        )
        self.submit_ans_btn.pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(
            direct_frame, text="취소(Esc)", font=("맑은 고딕", 8),
            bg=self.colors["btn_bg"], fg=self.colors["muted"], relief="flat",
            padx=6, pady=2, cursor="hand2", command=self.release_entry_focus
        ).pack(side=tk.LEFT)

        # 알파벳 A~Z 버튼 키보드
        keyboard_frame = tk.Frame(self.root, bg=self.colors["bg"])
        keyboard_frame.pack(pady=6)

        for idx, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            btn = tk.Button(
                keyboard_frame, text=letter, width=4, height=1,
                font=("Consolas", 11, "bold"),
                bg=self.colors["btn_bg"], fg=self.colors["btn_fg"],
                activebackground=self.colors["neon_blue"], activeforeground="#0F172A",
                disabledforeground="#475569", relief="flat", cursor="hand2",
                command=lambda ch=letter: self.on_letter_click(ch),
            )
            btn.grid(row=idx // 9, column=idx % 9, padx=3, pady=3)
            self.letter_buttons[letter] = btn

        # 하단 진행 버튼
        self.action_btn = tk.Button(
            self.root, text="▶ 다음 스테이지", font=("맑은 고딕", 10, "bold"),
            bg=self.colors["neon_blue"], fg="#0F172A", relief="flat",
            width=28, pady=6, cursor="hand2", command=self.next_round
        )
        self.action_btn.pack(pady=10)

        self.next_round()

    def exit_to_menu(self):
        """플레이 도중 메인 메뉴로 나갈 때 누적 점수를 저장할지 확인합니다."""
        if self.score > 0 and not self.is_game_over:
            if messagebox.askyesno("기록 저장", f"현재까지 얻은 {self.score}점을 온라인 랭킹에 저장할까요?"):
                self.save_ranking(self.player_nickname, self.score)
        self.show_menu_screen()

    def next_round(self):
        """단어장에서 무작위 단어를 뽑아 새 라운드를 시작합니다."""
        self.secret_word = random.choice(self.word_pool)
        self.guessed_letters.clear()
        self.wrong_count = 0
        self.is_game_over = False

        self.info_label.config(
            text=f"숨겨진 영단어를 추리하세요! (총 {len(self.secret_word)}글자 | 남은 기회: 6번)",
            fg="white",
        )
        self.word_label.config(fg="white")
        self.draw_gallows()
        self.update_word_display()
        self.set_inputs_state("normal")
        self.root.focus_set()

    # =========================================================================
    # 6. 정답 판정 및 점수 계산 로직
    # =========================================================================
    def on_letter_click(self, letter):
        self.root.focus_set()
        self.guess_letter(letter)

    def handle_keypress(self, event):
        if isinstance(event.widget, tk.Entry) or self.is_game_over:
            return
        pressed = event.char.upper()
        if pressed in self.letter_buttons and pressed not in self.guessed_letters:
            self.guess_letter(pressed)

    def guess_letter(self, letter):
        """알파벳 1글자 입력 시 정답 여부를 판정합니다."""
        self.letter_buttons[letter].config(state="disabled", bg=self.colors["card"])
        self.guessed_letters.add(letter)

        if letter in self.secret_word:
            self.update_word_display()
            self.combo += 1
            self.score += 100 * self.combo
            self.score_label.config(text=f"SCORE: {self.score}")
            self.combo_label.config(
                text=f"{self.combo} COMBO 🔥" if self.combo >= 2 else f"{self.combo} COMBO"
            )

            if set(self.secret_word).issubset(self.guessed_letters):
                bonus = (self.max_attempts - self.wrong_count) * 50
                self.score += bonus
                self.score_label.config(text=f"SCORE: {self.score}")
                self.finish_round(is_win=True, msg=f"🎉 스테이지 클리어! 남은 기회 보너스 +{bonus}점!")
        else:
            self.apply_wrong_penalty(f"'{letter}' 없음!")

    def submit_full_word(self):
        """입력창에 적은 전체 단어의 정답 여부를 판정합니다."""
        if self.is_game_over or not self.answer_entry:
            return

        typed = self.answer_entry.get().strip().upper()
        self.release_entry_focus()
        if not typed:
            return

        if typed == self.secret_word:
            unrevealed = len(set(self.secret_word) - self.guessed_letters)
            early_bonus = (unrevealed * 150) + ((self.max_attempts - self.wrong_count) * 50)
            self.score += 300 + early_bonus
            self.score_label.config(text=f"SCORE: {self.score}")
            self.finish_round(is_win=True, msg=f"🎯 한 번에 정답 적중! 보너스 +{early_bonus}점!")
        else:
            self.apply_wrong_penalty(f"'{typed}' 오답!")

    def apply_wrong_penalty(self, reason):
        """오답 시 콤보 초기화 및 행맨 1획 추가를 처리합니다."""
        self.wrong_count += 1
        self.combo = 0
        self.combo_label.config(text="0 COMBO")
        self.draw_hangman_part(self.wrong_count)

        remaining = self.max_attempts - self.wrong_count
        self.info_label.config(text=f"❌ {reason} 남은 기회: {remaining}번", fg=self.colors["neon_red"])

        if self.wrong_count >= self.max_attempts:
            self.finish_round(is_win=False, msg="💀 GAME OVER! 도전 실패!")

    def finish_round(self, is_win, msg):
        """라운드 종료 시 승리(다음 스테이지) 또는 패배(온라인 DB 랭킹 저장)를 처리합니다."""
        self.is_game_over = True
        self.set_inputs_state("disabled")

        if is_win:
            self.word_label.config(text=" ".join(self.secret_word), fg=self.colors["neon_green"])
            self.info_label.config(text=msg, fg=self.colors["neon_green"])
            self.action_btn.config(
                text="▶ 다음 스테이지 (점수 이어하기)",
                bg=self.colors["neon_green"],
                command=self.next_round,
            )
        else:
            final_score = self.score
            self.save_ranking(self.player_nickname, final_score)
            self.best_label.config(text=f"TOP 1: {self.get_best_score()}")

            self.word_label.config(text=" ".join(self.secret_word), fg=self.colors["neon_red"])
            self.info_label.config(
                text=f"{msg} (정답: {self.secret_word} | 최종 {final_score}점)",
                fg=self.colors["neon_red"],
            )
            self.action_btn.config(
                text="🏆 실시간 랭킹 보드에서 내 순위 확인하기",
                bg=self.colors["neon_yellow"],
                command=lambda: self.show_ranking_screen(self.player_nickname, final_score),
            )
            self.score = 0
            self.combo = 0

    def update_word_display(self):
        self.word_label.config(
            text=" ".join(ch if ch in self.guessed_letters else "_" for ch in self.secret_word)
        )

    def set_inputs_state(self, state):
        bg_color = self.colors["btn_bg"] if state == "normal" else self.colors["card"]
        for btn in self.letter_buttons.values():
            btn.config(state=state, bg=bg_color)
        if self.answer_entry:
            self.answer_entry.config(state=state)
        if self.submit_ans_btn:
            self.submit_ans_btn.config(state=state)

    # =========================================================================
    # 7. [화면 3] 실시간 명예의 전당 TOP 5 랭킹 보드
    # =========================================================================
    def show_ranking_screen(self, highlight_nick=None, highlight_score=None):
        self.clear_screen()
        self.is_game_over = True

        nav_bar = tk.Frame(self.root, bg=self.colors["bg"])
        nav_bar.pack(fill="x", padx=20, pady=(15, 5))

        tk.Button(
            nav_bar, text="🏠 메인 메뉴", font=("맑은 고딕", 9, "bold"),
            bg=self.colors["card"], fg="white", relief="flat",
            padx=10, pady=4, cursor="hand2", command=self.show_menu_screen
        ).pack(side=tk.LEFT)

        tk.Label(
            self.root, text="🏆 HALL OF FAME (TOP 5)", font=("Consolas", 22, "bold"),
            bg=self.colors["bg"], fg=self.colors["neon_yellow"]
        ).pack(pady=(15, 5))

        tk.Label(
            self.root, text="모든 플레이어와 실시간으로 공유되는 역대 최고 점수 순위입니다.",
            font=("맑은 고딕", 10), bg=self.colors["bg"], fg=self.colors["muted"]
        ).pack(pady=(0, 20))

        board = tk.Frame(self.root, bg=self.colors["card"], padx=20, pady=20)
        board.pack(fill="x", padx=40)

        header = tk.Frame(board, bg=self.colors["btn_bg"], pady=8)
        header.pack(fill="x", pady=(0, 8))
        tk.Label(header, text="순위", width=6, font=("맑은 고딕", 10, "bold"), bg=self.colors["btn_bg"], fg=self.colors["neon_blue"]).pack(side=tk.LEFT)
        tk.Label(header, text="닉네임", width=14, anchor="w", font=("맑은 고딕", 10, "bold"), bg=self.colors["btn_bg"], fg="white").pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="점수", width=10, anchor="e", font=("맑은 고딕", 10, "bold"), bg=self.colors["btn_bg"], fg=self.colors["neon_green"]).pack(side=tk.LEFT)
        tk.Label(header, text="달성 일시", width=16, anchor="e", font=("맑은 고딕", 10, "bold"), bg=self.colors["btn_bg"], fg=self.colors["muted"]).pack(side=tk.RIGHT, padx=8)

        rankings = self.get_top_rankings(limit=5)
        medals = ["🥇 1위", "🥈 2위", "🥉 3위", "  4위", "  5위"]

        if not rankings:
            tk.Label(
                board, text="아직 등록된 기록이 없거나 네트워크 연결 중입니다.\n첫 번째 주인공이 되어보세요!",
                font=("맑은 고딕", 11), bg=self.colors["card"], fg=self.colors["muted"], pady=40
            ).pack()
        else:
            for idx, (nick, sc, dt) in enumerate(rankings):
                is_me = (nick == highlight_nick and sc == highlight_score)
                row_bg = "#283548" if is_me else self.colors["card"]
                row = tk.Frame(board, bg=row_bg, pady=9)
                row.pack(fill="x", pady=2)

                rank_fg = self.colors["neon_yellow"] if idx == 0 else "white"
                tk.Label(row, text=medals[idx], width=6, font=("맑은 고딕", 10, "bold"), bg=row_bg, fg=rank_fg).pack(side=tk.LEFT)
                tk.Label(row, text=nick, width=14, anchor="w", font=("맑은 고딕", 10, "bold"), bg=row_bg, fg=self.colors["neon_blue"] if is_me else "white").pack(side=tk.LEFT, padx=5)
                tk.Label(row, text=f"{sc:,}점", width=10, anchor="e", font=("Consolas", 11, "bold"), bg=row_bg, fg=self.colors["neon_green"]).pack(side=tk.LEFT)
                tk.Label(row, text=dt, width=16, anchor="e", font=("Consolas", 9), bg=row_bg, fg=self.colors["muted"]).pack(side=tk.RIGHT, padx=8)

        tk.Button(
            self.root, text="🕹️ 지금 바로 도전하기", font=("맑은 고딕", 11, "bold"),
            bg=self.colors["neon_blue"], fg="#0F172A", relief="flat",
            width=24, pady=8, cursor="hand2", command=self.start_game_screen
        ).pack(pady=25)

    # =========================================================================
    # 8. 행맨 캔버스 드로잉
    # =========================================================================
    def draw_gallows(self):
        self.canvas.delete("all")
        self.canvas.create_line(45, 168, 140, 168, width=4, fill="#64748B")
        self.canvas.create_line(92, 168, 92, 18, width=4, fill="#64748B")
        self.canvas.create_line(92, 18, 180, 18, width=4, fill="#64748B")
        self.canvas.create_line(180, 18, 180, 40, width=3, fill="#94A3B8")

    def draw_hangman_part(self, step):
        c = self.colors["neon_red"]
        if step == 1:
            self.canvas.create_oval(162, 40, 198, 76, width=3, outline=c)
        elif step == 2:
            self.canvas.create_line(180, 76, 180, 124, width=3, fill=c)
        elif step == 3:
            self.canvas.create_line(180, 90, 155, 114, width=3, fill=c)
        elif step == 4:
            self.canvas.create_line(180, 90, 205, 114, width=3, fill=c)
        elif step == 5:
            self.canvas.create_line(180, 124, 160, 156, width=3, fill=c)
        elif step == 6:
            self.canvas.create_line(180, 124, 200, 156, width=3, fill=c)


if __name__ == "__main__":
    root = tk.Tk()
    game = SoloHangmanGame(root)
    root.mainloop()