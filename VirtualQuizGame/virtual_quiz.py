import cv2
import time
import numpy as np
import csv
import random
from cvzone.HandTrackingModule import HandDetector

# =========================
# CONFIG
# =========================
WIDTH, HEIGHT = 1280, 720
CLICK_THRESHOLD = 40  
SMOOTHING = 5
QUESTION_TIME = 10  
TOTAL_SOAL_KUIS = 5  # Tetap menampilkan 5 soal acak dari total 50 soal

START, QUIZ, FINISH = 0, 1, 2

# =========================
# PALET WARNA MODERN (Format BGR OpenCV)
# =========================
COLOR_BG_LIGHT   = (248, 249, 250)  # Putih Bersih (Off-White)
COLOR_PRIMARY    = (74, 35, 14)     # Deep Midnight Navy (Biru Gelap Elegan)
COLOR_TEXT_LIGHT = (255, 255, 255)  # Teks Putih
COLOR_TEXT_DARK  = (43, 43, 43)     # Teks Hitam Charcoal

COLOR_ACCENT_CYAN = (254, 242, 0)   # Cyan Elektrik Menyala (Efek Klik)
COLOR_TIMER_BAR   = (141, 134, 255) # Pastel Red/Salmon (Bar Waktu)
COLOR_PROGRESS    = (135, 211, 46)  # Mint Green Segar (Progress Bar Soal)
COLOR_CURSOR_IDLE = (204, 114, 245) # Lavender (Kursor Melayang)
COLOR_CURSOR_TAP  = (76, 217, 100)  # Hijau Emerald (Kursor saat Klik)

# =========================
# LOAD QUESTIONS FROM CSV
# =========================
def load_questions_from_csv(filename="soal.csv"):
    all_questions = []
    try:
        with open(filename, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            header = next(reader)  # Melewati baris pertama (judul kolom)
            for row in reader:
                if len(row) >= 6:  # Diperbarui jadi minimal 6 kolom (Soal + 4 Opsi + Jawaban)
                    soal = row[0]
                    pilihan = [row[1], row[2], row[3], row[4]]
                    jawaban_benar = int(row[5])
                    all_questions.append((soal, pilihan, jawaban_benar))
    except FileNotFoundError:
        print(f"Peringatan: File '{filename}' tidak ditemukan! Menggunakan soal cadangan.")
        all_questions = [("File CSV tidak ditemukan!", ["Opsi A", "Opsi B", "Opsi C", "Opsi D"], 0)]
    return all_questions

# Load semua bank soal yang ada di CSV
pool_questions = load_questions_from_csv("soal.csv")

# Ambil 5 soal secara acak untuk sesi pertama
questions = random.sample(pool_questions, min(TOTAL_SOAL_KUIS, len(pool_questions)))

# =========================
# INIT
# =========================
cap = cv2.VideoCapture(0)
cap.set(3, WIDTH)
cap.set(4, HEIGHT)

detector = HandDetector(detectionCon=0.8, maxHands=1)

game_state = START
current_q = 0
score = 0

tap_ready = True  
smooth_buffer = []
question_start_time = time.time()

# =========================
# UI FUNCTIONS
# =========================
def draw_button(img, text, x, y, w, h, bg_color, text_color=COLOR_TEXT_LIGHT):
    """Menggambar tombol estetik dengan sudut tegas & bayangan tipis"""
    cv2.rectangle(img, (x+2, y+4), (x+w+2, y+h+4), (50, 50, 50), cv2.FILLED)
    cv2.rectangle(img, (x, y), (x+w, y+h), bg_color, cv2.FILLED)
    
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
    text_x = x + (w - text_size[0]) // 2
    text_y = y + (h + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)

def draw_header_box(img, text, x, y, w, h):
    """Kotak putih kontras tinggi khusus untuk teks soal kuis"""
    cv2.rectangle(img, (x+3, y+4), (x+w+3, y+h+4), (80, 80, 80), cv2.FILLED)
    cv2.rectangle(img, (x, y), (x+w, y+h), COLOR_BG_LIGHT, cv2.FILLED)
    cv2.rectangle(img, (x, y), (x+w, y+h), COLOR_PRIMARY, 2)
    
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
    text_x = x + (w - text_size[0]) // 2
    text_y = y + (h + text_size[1]) // 2
    cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, COLOR_TEXT_DARK, 2)

def smooth_point(x, y):
    smooth_buffer.append((x, y))
    if len(smooth_buffer) > SMOOTHING:
        smooth_buffer.pop(0)
    avg = np.mean(smooth_buffer, axis=0)
    return int(avg[0]), int(avg[1])

# =========================
# MAIN LOOP
# =========================
while True:
    success, img = cap.read()
    if not success:
        break
        
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img, flipType=False)

    index_x, index_y = None, None
    tapped = False

    if hands:
        lmList = hands[0]["lmList"]
        p8 = lmList[8][:2]   
        p12 = lmList[12][:2] 

        index_x, index_y = smooth_point(p8[0], p8[1])

        try:
            length, info, img = detector.findDistance(p8, p12, img)

            if length < CLICK_THRESHOLD:
                if tap_ready:
                    tapped = True
                    tap_ready = False  
                cv2.circle(img, (index_x, index_y), 15, COLOR_CURSOR_TAP, cv2.FILLED)
                cv2.circle(img, (index_x, index_y), 15, (255, 255, 255), 2)
            else:
                tap_ready = True  
                cv2.circle(img, (index_x, index_y), 12, COLOR_CURSOR_IDLE, cv2.FILLED)
                cv2.circle(img, (index_x, index_y), 12, (255, 255, 255), 2)
                
        except Exception as e:
            pass
            
    # =========================
    # STATE: START
    # =========================
    if game_state == START:
        cv2.rectangle(img, (340, 130), (940, 250), COLOR_BG_LIGHT, cv2.FILLED)
        cv2.rectangle(img, (340, 130), (940, 250), COLOR_PRIMARY, 3)
        cv2.putText(img, "VIRTUAL QUIZ IT", (415, 205), cv2.FONT_HERSHEY_SIMPLEX, 1.6, COLOR_TEXT_DARK, 5)

        draw_button(img, "MULAI KUIS", 515, 380, 250, 80, COLOR_PROGRESS, COLOR_TEXT_DARK)

        if tapped and index_x:
            if 515 < index_x < 765 and 380 < index_y < 460:
                draw_button(img, "MULAI KUIS", 515, 380, 250, 80, COLOR_ACCENT_CYAN, COLOR_TEXT_DARK)
                cv2.imshow("Virtual Quiz IT", img)
                cv2.waitKey(1)
                time.sleep(0.3)
                
                game_state = QUIZ
                current_q = 0
                score = 0
                question_start_time = time.time()

    # =========================
    # STATE: QUIZ
    # =========================
    elif game_state == QUIZ:
        if current_q >= len(questions):
            game_state = FINISH
        else:
            q, opts, ans = questions[current_q]

            # ===== 1. BAR TIMER =====
            elapsed = time.time() - question_start_time
            remaining = max(0, QUESTION_TIME - elapsed)
            time_progress = remaining / QUESTION_TIME

            cv2.rectangle(img, (240, 45), (240 + int(800 * time_progress), 55), COLOR_TIMER_BAR, cv2.FILLED)
            cv2.rectangle(img, (240, 45), (1040, 55), COLOR_PRIMARY, 2)
            cv2.putText(img, f"Sisa Waktu: {int(remaining)}s", (240, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_TEXT_DARK, 2)

            if remaining <= 0:
                current_q += 1
                question_start_time = time.time()

            # Wadah Kotak Soal (Dibuat agak tipis menyesuaikan ruang tombol baru)
            draw_header_box(img, q, 140, 80, 1000, 75)

            # Render 4 Pilihan Jawaban (Tinggi diperkecil ke 60px & Jarak disesuaikan)
            buttons = []
            for i, opt in enumerate(opts):
                x = 240
                y = 175 + i * 85  # Offset baru agar muat 4 baris tombol jawaban
                draw_button(img, opt, x, y, 800, 60, COLOR_PRIMARY, COLOR_TEXT_LIGHT)
                buttons.append((x, y, 800, 60))

            # ===== 2. PROGRESS BAR SOAL =====
            q_progress = current_q / len(questions)
            percentage = int(q_progress * 100)
            
            # Posisi bar digeser sedikit ke bawah layar (Y: 535) agar tidak menabrak tombol ke-4
            cv2.rectangle(img, (240, 535), (1040, 560), (230, 230, 230), cv2.FILLED) 
            cv2.rectangle(img, (240, 535), (240 + int(800 * q_progress), 560), COLOR_PROGRESS, cv2.FILLED) 
            cv2.rectangle(img, (240, 535), (1040, 560), COLOR_PRIMARY, 2) 
            
            cv2.putText(img, f"Progres Kuis: {percentage}% ({current_q} dari {len(questions)} Soal)", 
                        (240, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.65, COLOR_TEXT_DARK, 2)

            if tapped and index_x:
                for i, (x, y, w, h) in enumerate(buttons):
                    if x < index_x < x+w and y < index_y < y+h:
                        if i == ans:
                            score += 1
                        
                        draw_button(img, opts[i], x, y, w, h, COLOR_ACCENT_CYAN, COLOR_TEXT_DARK)
                        cv2.imshow("Virtual Quiz IT", img)
                        cv2.waitKey(1)
                        
                        time.sleep(0.5)  
                        smooth_buffer.clear()
                        tap_ready = False  

                        current_q += 1
                        question_start_time = time.time()
                        break

    # =========================
    # STATE: FINISH
    # =========================
    elif game_state == FINISH:
        final_percentage = int((score / len(questions)) * 100)

        cv2.rectangle(img, (340, 140), (940, 320), COLOR_BG_LIGHT, cv2.FILLED)
        cv2.rectangle(img, (340, 140), (940, 320), COLOR_PROGRESS, 3)

        cv2.putText(img, "QUIZ SELESAI!", (470, 210), cv2.FONT_HERSHEY_SIMPLEX, 1.5, COLOR_PROGRESS, 4)
        cv2.putText(img, f"Nilai Akhir Kamu: {final_percentage}%", (440, 280), cv2.FONT_HERSHEY_SIMPLEX, 1.1, COLOR_TEXT_DARK, 3)

        draw_button(img, "ULANGI", 390, 390, 220, 75, (71, 141, 241), COLOR_TEXT_LIGHT) 
        draw_button(img, "KELUAR", 670, 390, 220, 75, (80, 80, 244), COLOR_TEXT_LIGHT)  

        if tapped and index_x:
            if 390 < index_x < 610 and 390 < index_y < 465:
                draw_button(img, "ULANGI", 390, 390, 220, 75, COLOR_ACCENT_CYAN, COLOR_TEXT_DARK)
                cv2.imshow("Virtual Quiz IT", img)
                cv2.waitKey(1)
                time.sleep(0.3)
                
                # Mengambil 5 kombinasi soal acak baru lagi dari kumpulan 50 soal di CSV
                questions = random.sample(pool_questions, min(TOTAL_SOAL_KUIS, len(pool_questions)))
                
                game_state = START
                smooth_buffer.clear()
                
            elif 670 < index_x < 890 and 390 < index_y < 465:
                draw_button(img, "KELUAR", 670, 390, 220, 75, COLOR_ACCENT_CYAN, COLOR_TEXT_DARK)
                cv2.imshow("Virtual Quiz IT", img)
                cv2.waitKey(1)
                time.sleep(0.3)
                break

    cv2.imshow("Virtual Quiz IT", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()