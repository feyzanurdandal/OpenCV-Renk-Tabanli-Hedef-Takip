import cv2
import numpy as np

# PC kamerasını başlat (Genellikle 0, harici kamera varsa 1 veya 2 dene)
cap = cv2.VideoCapture(0)

# Pencereleri oluştur ve yerlerini ayarla
cv2.namedWindow('Tespit', cv2.WINDOW_NORMAL)
cv2.namedWindow('Maske', cv2.WINDOW_NORMAL)
cv2.moveWindow('Tespit', 0, 0)
cv2.moveWindow('Maske', 700, 0)

print("🚀 PC Kamerası üzerinden tespit başlatıldı. Çıkış için 'q' tuşuna basın.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Kameradan görüntü alınamadı!")
        break

    # Görüntüyü yumuşat (Gürültüyü azaltmak için)
    blurred = cv2.medianBlur(frame, 5)

    # ── 1. ADIM: HSV MASKESİ (Renk Tonu Odaklı) ────────────────────────
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    # Koyu kırmızı aralığı
    lower_dark1 = np.array([0, 170, 25])
    upper_dark1 = np.array([10, 255, 255])
    lower_dark2 = np.array([170, 170, 25])
    upper_dark2 = np.array([180, 255, 255])
    
    mask_dark = cv2.bitwise_or(
        cv2.inRange(hsv, lower_dark1, upper_dark1),
        cv2.inRange(hsv, lower_dark2, upper_dark2)
    )

    # Açık/Parlak kırmızı aralığı
    lower_bright1 = np.array([170, 120, 50])
    upper_bright1 = np.array([180, 255, 255])
    lower_bright2 = np.array([0, 120, 50])
    upper_bright2 = np.array([10, 255, 255])
    
    mask_bright = cv2.bitwise_or(
        cv2.inRange(hsv, lower_bright1, upper_bright1),
        cv2.inRange(hsv, lower_bright2, upper_bright2)
    )

    mask_hsv = cv2.bitwise_or(mask_dark, mask_bright)

    # ── 2. ADIM: LAB MASKESİ (Kahve/Gürültü Bariyeri) ──────────────────
    # Kırmızıyı kahverengiden ayırmak için A kanalına (155+) kilitleniyoruz
    lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
    lower_lab = np.array([15, 155, 125])
    upper_lab = np.array([230, 255, 175])
    mask_lab = cv2.inRange(lab, lower_lab, upper_lab)

    # ── 3. ADIM: HİBRİT BİRLEŞTİRME (AND) ─────────────────────────────
    # Hem HSV hem LAB onay verirse 'Gerçek Kırmızı' kabul edilir
    red_mask = cv2.bitwise_and(mask_hsv, mask_lab)

    # ── 4. ADIM: TEMİZLİK (Morfoloji) ──────────────────────────────────
    kernel = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)

    # Sonucu orijinal görüntü üzerinde göster
    result = frame.copy()

    # ── 5. ADIM: KONTUR VE TESPİT ──────────────────────────────────────
    contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 600:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h
            
            # Nesnenin kareye yakınlığını kontrol et (Kutu tespiti için)
            if 0.7 < aspect_ratio < 1.3:
                cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 3)
                cv2.putText(result, f"HEDEF ({int(area)})", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Pencereleri göster
    cv2.imshow('Maske', red_mask)
    cv2.imshow('Tespit', result)

    # 'q' tuşuna basılırsa döngüden çık
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()