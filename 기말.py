import tkinter as tk
from tkinter import messagebox
import requests
import random
import re
from datetime import datetime

# 온라인 연동 주소
WORD_LIST_URL = "https://raw.githubusercontent.com/yujin-76/hangman_txt/main/word.txt"
FIREBASE_URL = "https://hangman-ranking-default-rtdb.firebaseio.com"

# 기본 예비 단어 (인터넷 연결 실패 시 사용)
FALLBACK_WORDS = [
    "PYTHON", "COMPUTER", "ALGORITHM", "DATABASE", "NETWORK",
    "KEYBOARD", "SOFTWARE", "VARIABLE", "FUNCTION", "HANGMAN"
]


class SoloHangmanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("행맨 아케이드 온라인")
        self.root.geometry("540x680")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.words = []
        self.online_loaded = False
        self.nickname = ""
        self.score = 0
        self.streak = 0
        self.max_lives = 6
        self.lives = 6
        self.secret_word = ""
        self.guessed_letters = set()
        self.letter_buttons = {}

        self.fetch_words()
        self.show_lobby()

    def fetch_words(self):
        """GitHub에서 최신 단어장 불러오기"""
        try:
            res = requests.get(WORD_LIST_URL, timeout=5)
            if res.status_code == 200:
                lines = [
                    line.strip().upper()
                    for line in res.text.splitlines()
                    if line.strip().isalpha()
                ]
                if lines:
                    self.words = list(set(lines))
                    self.online_loaded = True
                    return
        except Exception as e:
            print("단어장 불러오기 실패:", e)

        self.words = FALLBACK_WORDS[:]
        self.online_loaded = False

    def clean_key(self, nickname):
        """Firebase 경로에 사용할 수 없는 특수문자 치환"""
        return re.sub(r'[.#$\[\]/]', '_', nickname).strip()

    def save_score(self, nickname, score):
        """닉네임별 기존 최고 기록보다 높을 때만 덮어쓰기"""
        if score <= 0:
            return
        key = self.clean_key(nickname)
        if not key:
            return

        url = f"{FIREBASE_URL}/rankings/{key}.json"
        try:
            res = requests.get(url, timeout=5)
            old_data = res.json() if res.status_code == 200 else None
            old_score = old_data.get("score", 0) if isinstance(old_data, dict) else 0

            if score > old_score:
                data = {
                    "nickname": nickname,
                    "score": score,
                    "played_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                requests.put(url, json=data, timeout=5)
        except Exception as e:
            print("랭킹 저장 실패:", e)

    def load_rankings(self):
        """Firebase에서 상위 5명 랭킹 불러오기"""
        url = f"{FIREBASE_URL}/rankings.json"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200 and res.json():
                raw_data = res.json()
                entries = [
                    item for item in raw_data.values()
                    if isinstance(item, dict) and "nickname" in item and "score" in item
                ]
                entries.sort(key=lambda x: x["score"], reverse=True)
                return entries[:5]
        except Exception as e:
            print("랭킹 조회 실패:", e)
        return []

    def clear_screen(self):
        self.root.unbind("<Key>")
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_lobby(self):
        """메인 로비 및 실시간 랭킹 화면"""
        self.clear_screen()

        tk.Label(
            self.root, text="HANGMAN ARCADE",
            font=("Consolas", 28, "bold"), fg="#89b4fa", bg="#1e1e2e"
        ).pack(pady=(35, 5))

        tk.Label(
            self.root, text="온라인 단어장 & 실시간 명예의 전당",
            font=("맑은 고딕", 11), fg="#bac2de", bg="#1e1e2e"
        ).pack(pady=(0, 25))

        # 닉네임 입력 영역
        input_frame = tk.Frame(self.root, bg="#1e1e2e")
        input_frame.pack(pady=10)

        tk.Label(
            input_frame, text="닉네임 :",
            font=("맑은 고딕", 12, "bold"), fg="#cdd6f4", bg="#1e1e2e"
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.nick_entry = tk.Entry(
            input_frame, font=("맑은 고딕", 12), width=16,
            justify="center", bg="#313244", fg="#ffffff",
            insertbackground="#ffffff", relief=tk.FLAT
        )
        self.nick_entry.pack(side=tk.LEFT, ipady=5)
        if self.nickname:
            self.nick_entry.insert(0, self.nickname)
        self.nick_entry.focus()

        tk.Button(
            self.root, text="▶ 게임 시작",
            font=("맑은 고딕", 13, "bold"), bg="#a6e3a1", fg="#11111b",
            activebackground="#94e2d5", width=20, height=2,
            relief=tk.FLAT, cursor="hand2", command=self.start_game
        ).pack(pady=(15, 25))

        # 실시간 명예의 전당 박스
        rank_box = tk.Frame(self.root, bg="#181825", padx=20, pady=15)
        rank_box.pack(fill=tk.X, padx=45)

        header_frame = tk.Frame(rank_box, bg="#181825")
        header_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            header_frame, text="🏆 실시간 명예의 전당 TOP 5",
            font=("맑은 고딕", 12, "bold"), fg="#f9e2af", bg="#181825"
        ).pack(side=tk.LEFT)

        tk.Button(
            header_frame, text="새로고침",
            font=("맑은 고딕", 9), bg="#313244", fg="#cdd6f4",
            relief=tk.FLAT, cursor="hand2", command=self.show_lobby
        ).pack(side=tk.RIGHT)

        rankings = self.load_rankings()
        if not rankings:
            tk.Label(
                rank_box, text="아직 등록된 랭킹이 없습니다. 첫 주인공이 되어보세요!",
                font=("맑은 고딕", 10), fg="#6c7086", bg="#181825"
            ).pack(pady=20)
        else:
            medals = ["🥇", "🥈", "🥉", "4위", "5위"]
            for idx, item in enumerate(rankings):
                row = tk.Frame(rank_box, bg="#181825")
                row.pack(fill=tk.X, pady=3)
                tk.Label(
                    row, text=f"{medals[idx]}  {item['nickname']}",
                    font=("맑은 고딕", 11, "bold" if idx < 3 else "normal"),
                    fg="#cdd6f4", bg="#181825"
                ).pack(side=tk.LEFT)
                tk.Label(
                    row, text=f"{item['score']}점",
                    font=("Consolas", 11, "bold"),
                    fg="#a6e3a1", bg="#181825"
                ).pack(side=tk.RIGHT)

        # 하단 단어장 연동 상태
        status_text = (
            f"📚 온라인 단어장 연동 완료 (총 {len(self.words)}개 단어 수록)"
            if self.online_loaded
            else f"⚠️ 오프라인 기본 단어장 사용 중 (총 {len(self.words)}개)"
        )
        tk.Label(
            self.root, text=status_text,
            font=("맑은 고딕", 9), fg="#a6adc8", bg="#1e1e2e"
        ).pack(side=tk.BOTTOM, pady=15)

    def start_game(self):
        nick = self.nick_entry.get().strip()
        if not nick:
            messagebox.showwarning("알림", "랭킹 등록을 위해 닉네임을 입력해주세요!")
            return
        if len(nick) > 12:
            messagebox.showwarning("알림", "닉네임은 12자 이내로 입력해주세요.")
            return

        self.nickname = nick
        self.score = 0
        self.streak = 0
        self.next_round()

    def next_round(self):
        self.lives = self.max_lives
        self.secret_word = random.choice(self.words)
        self.guessed_letters = set()
        self.build_game_ui()

    def build_game_ui(self):
        self.clear_screen()

        # 상단 상태 바
        top_bar = tk.Frame(self.root, bg="#181825", padx=20, pady=12)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar, text=f"플레이어: {self.nickname}",
            font=("맑은 고딕", 10, "bold"), fg="#cdd6f4", bg="#181825"
        ).pack(side=tk.LEFT)

        self.score_label = tk.Label(
            top_bar, text=f"점수: {self.score}점  |  연속 정답: {self.streak}",
            font=("맑은 고딕", 10, "bold"), fg="#a6e3a1", bg="#181825"
        )
        self.score_label.pack(side=tk.RIGHT)

        # 행맨 그림 캔버스
        self.canvas = tk.Canvas(
            self.root, width=260, height=220,
            bg="#1e1e2e", highlightthickness=0
        )
        self.canvas.pack(pady=(15, 5))
        self.draw_hangman()

        # 남은 목숨 표시
        self.lives_label = tk.Label(
            self.root, text=f"남은 기회: {'❤️ ' * self.lives}",
            font=("맑은 고딕", 11, "bold"), fg="#f38ba8", bg="#1e1e2e"
        )
        self.lives_label.pack(pady=5)

        # 단어 빈칸 표시
        self.word_label = tk.Label(
            self.root, text=self.get_masked_word(),
            font=("Consolas", 26, "bold"), fg="#f9e2af", bg="#1e1e2e"
        )
        self.word_label.pack(pady=(10, 20))

        # 알파벳 버튼 키패드
        keypad = tk.Frame(self.root, bg="#1e1e2e")
        keypad.pack(pady=5)

        self.letter_buttons = {}
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for idx, char in enumerate(alphabet):
            btn = tk.Button(
                keypad, text=char, font=("Consolas", 11, "bold"),
                width=4, height=1, bg="#313244", fg="#cdd6f4",
                activebackground="#45475a", relief=tk.FLAT, cursor="hand2",
                command=lambda c=char: self.guess_letter(c)
            )
            btn.grid(row=idx // 9, column=idx % 9, padx=3, pady=3)
            self.letter_buttons[char] = btn

        # 키보드 입력 지원
        self.root.bind("<Key>", self.on_key_press)

    def on_key_press(self, event):
        char = event.char.upper()
        if char in self.letter_buttons:
            self.guess_letter(char)

    def get_masked_word(self):
        return " ".join([c if c in self.guessed_letters else "_" for c in self.secret_word])

    def draw_hangman(self):
        self.canvas.delete("all")
        wrong = self.max_lives - self.lives
        # 교수대
        self.canvas.create_line(40, 200, 160, 200, width=4, fill="#6c7086")
        self.canvas.create_line(80, 200, 80, 25, width=4, fill="#6c7086")
        self.canvas.create_line(80, 25, 175, 25, width=4, fill="#6c7086")
        self.canvas.create_line(175, 25, 175, 50, width=3, fill="#6c7086")

        if wrong >= 1:  # 머리
            self.canvas.create_oval(155, 50, 195, 90, width=3, outline="#f38ba8")
        if wrong >= 2:  # 몸통
            self.canvas.create_line(175, 90, 175, 145, width=3, fill="#f38ba8")
        if wrong >= 3:  # 왼팔
            self.canvas.create_line(175, 105, 148, 130, width=3, fill="#f38ba8")
        if wrong >= 4:  # 오른팔
            self.canvas.create_line(175, 105, 202, 130, width=3, fill="#f38ba8")
        if wrong >= 5:  # 왼다리
            self.canvas.create_line(175, 145, 152, 180, width=3, fill="#f38ba8")
        if wrong >= 6:  # 오른다리
            self.canvas.create_line(175, 145, 198, 180, width=3, fill="#f38ba8")

    def guess_letter(self, char):
        if char in self.guessed_letters:
            return

        self.guessed_letters.add(char)
        btn = self.letter_buttons[char]
        btn.config(state=tk.DISABLED)

        if char in self.secret_word:
            btn.config(bg="#a6e3a1", disabledforeground="#11111b")
            self.word_label.config(text=self.get_masked_word())

            # 단어 완성 체크
            if all(c in self.guessed_letters for c in self.secret_word):
                self.streak += 1
                bonus = self.lives * 10 + self.streak * 20
                self.score += 100 + bonus
                messagebox.showinfo(
                    "정답!",
                    f"단어 '{self.secret_word}' 성공!\n획득 점수: +{100 + bonus}점 (현재 총점: {self.score}점)"
                )
                self.next_round()
        else:
            btn.config(bg="#f38ba8", disabledforeground="#11111b")
            self.lives -= 1
            self.draw_hangman()
            self.lives_label.config(
                text=f"남은 기회: {'❤️ ' * self.lives}" if self.lives > 0 else "남은 기회: 0"
            )

            if self.lives <= 0:
                self.save_score(self.nickname, self.score)
                messagebox.showinfo(
                    "게임 오버",
                    f"아쉽습니다! 정답은 '{self.secret_word}' 였습니다.\n최종 점수: {self.score}점"
                )
                self.show_lobby()


if __name__ == "__main__":
    root = tk.Tk()
    game = SoloHangmanGame(root)
    root.mainloop()