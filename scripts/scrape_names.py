import requests
from bs4 import BeautifulSoup
import json
import time
import re
import sys

# Türkçe karakterler için stdout ayarı
sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_URL = "https://anitsayac.com/"

def clean_text(text):
    if not text: return None
    text = text.replace('\xa0', ' ').replace('\r', '').replace('\n', '').strip()
    return text if len(text) > 1 else None

def get_value_from_bold_tag(soup, keywords):
    all_bolds = soup.find_all("b")
    for b in all_bolds:
        if not b.string: continue
        b_text = b.string.lower().strip()
        for key in keywords:
            if key in b_text:
                sibling = b.next_sibling
                for _ in range(3): 
                    if not sibling: break
                    if isinstance(sibling, str):
                        cleaned = clean_text(sibling)
                        if cleaned: return cleaned
                    sibling = sibling.next_sibling
    return "Bilinmiyor"

def extract_source_link(soup):
    try:
        source_label = soup.find("b", string=re.compile("Kaynak", re.IGNORECASE))
        if source_label:
            link = source_label.find_next("a")
            if link: return link.get("href")
    except:
        pass
    return ""

def main():
    print("TÜM VERİLERİ ÇEKME İŞLEMİ BAŞLIYOR...", flush=True)
    
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=60)
        soup = BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        print(f"Ana sayfaya bağlanılamadı: {e}")
        return

    # Tüm linkleri al
    links = soup.select("span.xxy a")
    total_links = len(links)
    print(f"Toplam {total_links} kayıt bulundu. Hepsi işlenecek.", flush=True)
    
    all_data = []
    
    # LİMİTİ KALDIRDIK: target_links = links
    target_links = links 

    # Her 100 kişide bir dosyayı kaydetmek istersen (Opsiyonel güvenlik)
    save_interval = 100

    start_time = time.time()

    for index, link in enumerate(target_links):
        try:
            name = clean_text(link.get_text())
            if not name: continue
            
            href = link.get("href")
            if not href: continue
            
            full_url = BASE_URL + href
            
            # Detay çekme (Hata olursa pas geçme, retry yapabiliriz ama basit tutalım)
            try:
                det_req = requests.get(full_url, headers=HEADERS, timeout=15)
                det_req.encoding = det_req.apparent_encoding
                det_soup = BeautifulSoup(det_req.text, "html.parser")
                
                person_data = {
                    "name": name,
                    "age": get_value_from_bold_tag(det_soup, ["yaşı", "yasi", "yas"]),
                    "location": get_value_from_bold_tag(det_soup, ["il/ilçe", "ilçe", "sehir"]),
                    "date": get_value_from_bold_tag(det_soup, ["tarih"]),
                    "reason": get_value_from_bold_tag(det_soup, ["neden", "sebep"]),
                    "killer": get_value_from_bold_tag(det_soup, ["kim tarafından", "fail"]),
                    "protection": get_value_from_bold_tag(det_soup, ["korunma", "tedbir"]),
                    "method": get_value_from_bold_tag(det_soup, ["şekli", "sekli", "silah"]),
                    "status": get_value_from_bold_tag(det_soup, ["failin durumu", "durumu"]),
                    "source": extract_source_link(det_soup)
                }
                
                all_data.append(person_data)
                
                # İlerleme çubuğu gibi konsola yaz
                if index % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"[{index+1}/{total_links}] İşlenen: {name} (Geçen süre: {int(elapsed)}sn)", flush=True)

            except Exception as e:
                print(f"HATA ({name}): {e}")
                # Detay alınamasa bile ismi kaydet
                all_data.append({"name": name, "date": "Veri Alınamadı"})
            
            # Siteyi çok yormamak için bekleme (Çok önemli)
            time.sleep(0.15) 

        except Exception as e:
            continue

    # İşlem bitince kaydet
    with open("anit_verileri.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    print(f"BİTTİ! Toplam {len(all_data)} veri anit_verileri.json dosyasına yazıldı.")

if __name__ == "__main__":
    main()
