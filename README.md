# Personal Data Guardian

**Personal Data Guardian**, kullanıcıların kendi dijital ayak izlerini test ederek kişisel gizlilik seviyelerini daha iyi anlamalarına yardımcı olan bir farkındalık aracıdır.  
Verilen bilgiler üzerinden bir **gizlilik skoru**, **risk analizi** ve **e-posta dijital izi raporu** üretir.

---

## Özellikler

### Gizlilik Skoru
Girilen bilgilere göre 0–100 aralığında otomatik gizlilik skoru hesaplanır.

### Risk Analizi
- HIGH / MEDIUM / LOW seviyelerinde kategorize edilmiş riskler  
- Her risk için açıklama + önerilen aksiyon  
- Tekrarlanan e-posta kullanımı  
- Konum / telefon gibi hassas bilgiler  
- Profil görünürlüğü  
- Username–email eşleşmeleri

### 📧 E-posta Dijital İzi Analizi
- Örnek sızıntı kaynakları  
- GitHub commit izleri (örnekleştirilmiş)  
- Keybase profil kontrolleri  
- E-posta görünürlük riskleri

### 🌐 Çoklu Platform Analizi
Instagram, LinkedIn, GitHub vb. platformlar için:  
- Kullanıcı adı  
- E-posta  
- Bio  
- Profil açıklığı  
- Telefon/konum bilgisi tespiti

---

# Lokal Kurulum

Uygulama **backend (FastAPI)** ve **frontend (React + Vite + TypeScript)** olarak iki ayrı yapıda çalışır.

---

## Backend (FastAPI)

### Gereksinimler
- Python 3.10+
- pip

### Kurulum

```bash
cd backend
python -m venv venv
source venv/bin/activate   
pip install -r requirements.txt
