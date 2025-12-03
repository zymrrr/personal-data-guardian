# Personal Data Guardian

Kullanıcıların kendi dijital ayak izlerini test edebildiği, **kişisel gizlilik skoru** ve **risk analizi** üreten mini bir web uygulaması.

- Backend: Python + FastAPI
- Frontend: React + TypeScript + Vite + Tailwind CSS
- Kullanım alanı: Kişisel gizlilik farkındalığı, demo amaçlı "privacy check" aracı

---

## Özellikler

- Ad, ana e-posta ve birden fazla sosyal medya hesabı (platform, kullanıcı adı, e-posta, bio, telefon/konum bilgisi) üzerinden analiz
- 0–100 arası **gizlilik skoru**
- HIGH / MEDIUM / LOW seviyelerinde detaylı **risk listesi** ve öneriler
- **E-posta Dijital İzi** kartı:
  - Sızıntı kaynağı tespit edildi mi?
  - Öne çıkan kaynak listesi
  - GitHub commit izleri (örnekleştirilmiş)
  - Keybase profili kontrolü (örnekleştirilmiş)

Hiçbir kişisel veri kodun içinde gömülü değil; analiz tamamen kullanıcının lokal olarak girdiği bilgiler üzerinden yapılıyor.

---

## Lokal Kurulum

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows'ta: venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload --port 8000

# personal-data-guardian
