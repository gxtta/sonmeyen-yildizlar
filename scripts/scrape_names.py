import requests
from bs4 import BeautifulSoup
import json
import time
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_URL = "https://anitsayac.com/"

def clean_text(text):
    """HTML etiketlerinden arınmış temiz metin döndürür."""
    if not text: return "Bilinmiyor"
    # &nbsp; gibi boşlukları ve baştaki/sondaki boşlukları temizle
    return text.replace('\xa0', ' ').strip()

def get_detail_value(soup, key_text):
    """Verilen anahtar kelimeyi (örn: 'İl/ilçe') bulup yanındaki değeri döndürür."""
    try:
        # İçinde anahtar kelime geçen <b> etiketini bul
        label = soup.find("b", string=re.compile(re.escape(key_text)))
        if label and label.next_sibling:
            return clean_text(label.next_sibling)
    except:
        pass
    return "Bilinmiyor"

def main():
    print("Detaylı veri çekme işlemi başlıyor...")
    
    try:
        r = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        print(f"Ana sayfaya bağlanılamadı: {e}")
        return

    links = soup.select("span.xxy a")
    print(f"Toplam bulunan kayıt: {len(links)}")
    
    all_data = []
    
    # GÜVENLİK İÇİN LİMİT: GitHub Actions süresini aşmamak için
    # İlk seferde veya günlük güncellemede son 150 kişiyi çekmek mantıklıdır.
    # Hepsini çekmek isterseniz bu satırı: target_links = links
    # yapabilirsiniz ancak işlem 30-40 dakika sürebilir.
    target_links = links[:150] 

    print(f"{len(target_links)} kayıt detaylandırılacak...")

    for index, link in enumerate(target_links):
        try:
            name = clean_text(link.get_text())
            href = link.get("href")
            if not href: continue

            full_url = BASE_URL + href
            
            # Detay sayfasına git
            det_req = requests.get(full_url, headers=HEADERS, timeout=10)
            # Türkçe karakter sorunu olmaması için
            det_req.encoding = det_req.apparent_encoding
            det_soup = BeautifulSoup(det_req.text, "html.parser")
            
            # --- Verileri Ayıkla ---
            person_data = {
                "name": name,
                "age": get_detail_value(det_soup, "Maktülün yaşı:"),
                "location": get_detail_value(det_soup, "İl/ilçe:"),
                "date": get_detail_value(det_soup, "Tarih:"),
                "reason": get_detail_value(det_soup, "Neden öldürüldü:"),
                "killer": get_detail_value(det_soup, "Kim tarafından öldürüldü:"),
                "protection": get_detail_value(det_soup, "Korunma talebi:"),
                "method": get_detail_value(det_soup, "Öldürülme şekli:"),
                "status": get_detail_value(det_soup, "Failin durumu:"),
                "source": ""
            }

            # Kaynak Linkini Özel Olarak Al (Link olduğu için)
            try:
                source_label = det_soup.find("b", string=re.compile("Kaynak:"))
                if source_label:
                    # Kaynak etiketinden sonraki ilk <a> etiketini bul
                    # Bazen direkt yanında, bazen <br>den sonra olabilir.
                    # next_elements kullanarak ileriye doğru arıyoruz.
                    for elem in source_label.find_all_next("a", limit=1):
                        person_data["source"] = elem.get("href")
            except:
                person_data["source"] = ""

            # Konsola bilgi bas
            print(f"[{index+1}/{len(target_links)}] {name} ({person_data['date']})")
            
            all_data.append(person_data)
            
            # Siteyi yormamak için bekle
            time.sleep(0.2) 

        except Exception as e:
            print(f"Hata ({name}): {e}")
            continue

    # JSON Kaydet
    with open("anit_verileri.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)
    
    print(f"İşlem tamamlandı. Toplam {len(all_data)} veri kaydedildi.")

if __name__ == "__main__":
    main()
