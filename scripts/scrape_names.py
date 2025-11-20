import requests
from bs4 import BeautifulSoup
import json
import time
import os

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
BASE_URL = "https://anitsayac.com/"

def main():
    print("Veri çekme başladı...")
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        print(f"Hata: {e}")
        return

    links = soup.select("span.xxy a")
    print(f"Bulunan kişi sayısı: {len(links)}")
    
    all_data = []
    # Son 100 kişiyi çek (Hızlı olması için)
    target_links = links[:100] 

    for index, link in enumerate(target_links):
        try:
            name = link.get_text(strip=True)
            href = link.get("href")
            if not href: continue

            full_url = BASE_URL + href
            
            # Detay sayfasına git ve tarih bul
            try:
                det_req = requests.get(full_url, headers=HEADERS, timeout=10)
                det_req.encoding = det_req.apparent_encoding
                det_soup = BeautifulSoup(det_req.text, "html.parser")
                tarih_etiketi = det_soup.find("b", string=lambda t: t and "Tarih" in t)
                date_val = tarih_etiketi.next_sibling.strip() if (tarih_etiketi and tarih_etiketi.next_sibling) else "Tarih Bilinmiyor"
            except:
                date_val = "Tarih Bilinmiyor"

            print(f"{name} - {date_val}")
            all_data.append({"name": name, "date": date_val})
            time.sleep(0.2) 
        except:
            continue

    # JSON Kaydet
    with open("anit_verileri.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    print("Bitti.")

if __name__ == "__main__":
    main()
