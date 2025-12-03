from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple
import uuid
import re
import hashlib
from pathlib import Path

# httpx opsiyonel: yoksa sadece GitHub/Keybase kısımları None döner
try:
    import httpx  # type: ignore
except ImportError:
    httpx = None  # type: ignore

app = FastAPI(
    title="Personal Data Guardian API",
    description="Kişisel dijital gizlilik skorunu hesaplayan gelişmiş API",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================================================
#  Yardımcı normalizasyon (Türkçe karakterleri sadeleştir)
# ======================================================
TR_TABLE = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def norm(text: str) -> str:
    return text.lower().translate(TR_TABLE)


# ======================================================
#  Türkiye il + bazı İstanbul ilçe anahtar kelimeleri
# ======================================================
TR_CITY_KEYWORDS = [
    "adana", "adiyaman", "afyonkarahisar", "agri", "amasya", "ankara",
    "antalya", "artvin", "aydin", "balikesir", "bilecik", "bingol", "bitlis",
    "bolu", "burdur", "bursa", "canakkale", "cankiri", "corum", "denizli",
    "diyarbakir", "edirne", "elazig", "erzincan", "erzurum", "eskisehir",
    "gaziantep", "giresun", "gumushane", "hakkari", "hatay", "isparta",
    "mersin", "istanbul", "izmir", "kars", "kastamonu", "kayseri",
    "kirklareli", "kirsehir", "kocaeli", "konya", "kutahya", "malatya",
    "manisa", "kahramanmaras", "mardin", "mugla", "mus", "nevsehir", "nigde",
    "ordu", "rize", "sakarya", "samsun", "siirt", "sinop", "sivas",
    "tekirdag", "tokat", "trabzon", "tunceli", "sanliurfa", "usak", "van",
    "yozgat", "zonguldak", "aksaray", "bayburt", "karaman", "kirikkale",
    "batman", "sirnak", "bartin", "ardahan", "igdir", "yalova", "karabuk",
    "kilis", "osmaniye", "duzce",
]

IST_DISTRICTS = [
    "esenler", "kadikoy", "uskudar", "fatih", "besiktas", "sariyer",
    "bakirkoy", "atasehir", "umraniye", "kartal", "pendik", "maltepe",
    "bayrampasa", "bahcelievler", "bagcilar", "basaksehir", "beylikduzu",
    "kucukcekmece", "buyukcekmece", "zeytinburnu", "gaziosmanpasa",
    "kagithane", "sisli", "beyoglu", "eyupsultan",
]

# 01–81 plaka kodu (başında/sonunda başka rakam yoksa)
PLATE_CODE_PATTERN = re.compile(r"(?<!\d)(0?[1-9]|[1-7][0-9]|8[01])(?!\d)")

# Adres benzeri patternler (mah, sok, no, daire vs.)
ADDRESS_HINTS = [
    "mah", "mah.", "mahalle",
    "sk", "sk.", "sok", "sokak",
    "cd", "cad", "cadde",
    "no:", "no ", "kapi no", "kapı no", "daire", "blok",
]

# Okul / kurum / banka vb. anahtar kelimeler (light)
ORG_KEYWORDS = [
    "universitesi", "lisesi", "koleji", "fakultesi",
    "bank", "banka", "holding", "sigorta",
    "a.s.", "a.s", "anonim", "sanayi", "ticaret",
]

GENERIC_LOCAL_PARTS = {
    "test", "deneme", "qwe", "asdf", "asd", "abc", "xyz", "user", "kullanici"
}

FREE_EMAIL_DOMAINS = {
    "gmail.com", "hotmail.com", "hotmail.com.tr", "outlook.com",
    "outlook.com.tr", "yahoo.com", "yandex.com", "icloud.com",
    "proton.me", "protonmail.com", "msn.com", "live.com", "live.com.tr",
}


def text_has_location(text: Optional[str]) -> bool:
    """Metin içerisinde il / ilçe / plaka kodu var mı?"""
    if not text:
        return False
    t = norm(text)
    if any(k in t for k in TR_CITY_KEYWORDS + IST_DISTRICTS):
        return True
    if PLATE_CODE_PATTERN.search(t):
        return True
    return False


def text_looks_like_address(text: Optional[str]) -> bool:
    if not text:
        return False
    t = norm(text)
    return any(h in t for h in ADDRESS_HINTS)


def text_has_org_hint(text: Optional[str]) -> bool:
    if not text:
        return False
    t = norm(text)
    return any(k in t for k in ORG_KEYWORDS)


def email_contains_4digit_year(email: str) -> bool:
    local = email.split("@")[0]
    digits = re.findall(r"\d{4}", local)
    for d in digits:
        year = int(d)
        if 1950 <= year <= 2035:
            return True
    return False


def email_contains_2digit_year(email: str) -> bool:
    local = email.split("@")[0]
    candidates = re.findall(r"(^|[^0-9])(\d{2})([^0-9]|$)", local)
    for _, d, _ in candidates:
        val = int(d)
        # 50–99 veya 00–24 → yıl gibi kabul
        if val >= 50 or val <= 24:
            return True
    return False


def email_looks_like_phone(email: str) -> bool:
    local = email.split("@")[0]
    digits = re.findall(r"\d+", local)
    for d in digits:
        if len(d) in (10, 11) and d[0] in ("0", "5"):
            return True
    return False


def email_local_too_generic(email: str) -> bool:
    local = email.split("@")[0].lower()
    if local in GENERIC_LOCAL_PARTS:
        return True
    if len(local) <= 3:
        return True
    return False


def split_email(email: str) -> Tuple[str, str]:
    email = email.strip().lower()
    if "@" not in email:
        return email, ""
    local, domain = email.split("@", 1)
    return local, domain


def is_corporate_email(email: str) -> bool:
    _, domain = split_email(email)
    if not domain:
        return False
    if domain in FREE_EMAIL_DOMAINS:
        return False
    return "." in domain


def normalize_name_tokens(full_name: str) -> List[str]:
    tokens = [t for t in re.split(r"\s+", norm(full_name)) if t]
    tokens = [t for t in tokens if len(t) >= 3]
    return tokens


# ======================================================
#  Email Exposure / Breach DB helper'ları
# ======================================================
BREACH_DB_LOADED = False
BREACH_DB: Dict[str, List[str]] = {}


def load_breach_db() -> None:
    """
    data/breach_hashes.txt dosyasını 1 kez belleğe alır.
    Format (satır başına):
        SHA1HASH;Kaynak1,Kaynak2
    Örn:
        a94a8fe5ccb19ba61c4c0873d391e987982fbbd3;Adobe 2013,Dropbox 2012
    """
    global BREACH_DB_LOADED, BREACH_DB
    if BREACH_DB_LOADED:
        return

    path = Path(__file__).parent / "data" / "breach_hashes.txt"
    if not path.exists():
        BREACH_DB_LOADED = True
        BREACH_DB = {}
        return

    db: Dict[str, List[str]] = {}
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or ";" not in line:
                continue
            sha1_hash, sources_str = line.split(";", 1)
            sha1_hash = sha1_hash.strip().lower()
            sources = [s.strip() for s in sources_str.split(",") if s.strip()]
            if sha1_hash:
                db[sha1_hash] = sources

    BREACH_DB = db
    BREACH_DB_LOADED = True


def check_breaches_for_email(email: str) -> Tuple[bool, List[str]]:
    """E-posta için local hash DB'de kayıt var mı, varsa kaynak listesi döner."""
    load_breach_db()
    if not BREACH_DB:
        return False, []

    normalized = email.strip().lower()
    sha1_hash = hashlib.sha1(normalized.encode("utf-8")).hexdigest()
    sources = BREACH_DB.get(sha1_hash, [])
    return (len(sources) > 0, sources)


def github_commit_count_for_email(email: str) -> Optional[int]:
    """Ücretsiz GitHub search API ile commit sayısını tahmini döner."""
    if httpx is None:
        return None
    try:
        url = f"https://api.github.com/search/commits?q=author-email:{email}"
        headers = {
            "Accept": "application/vnd.github.cloak-preview",
            "User-Agent": "personal-data-guardian",
        }
        resp = httpx.get(url, headers=headers, timeout=3.0)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return int(data.get("total_count", 0))
    except Exception:
        return None


def keybase_has_profile_for_email(email: str) -> Optional[bool]:
    """Email Keybase üzerinde bir profile bağlı mı?"""
    if httpx is None:
        return None
    try:
        url = f"https://keybase.io/_/api/1.0/user/lookup.json?email={email}"
        resp = httpx.get(url, timeout=3.0)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return bool(data.get("them"))
    except Exception:
        return None


# ======================================================
#  Pydantic Modelleri
# ======================================================
class SocialAccount(BaseModel):
    platform: str
    username: str
    email: Optional[str] = None
    is_public: bool = True
    has_phone_in_bio: bool = False
    has_location_in_bio: bool = False
    bio_text: Optional[str] = None


class AnalyzeRequest(BaseModel):
    full_name: str
    primary_email: str
    bio: Optional[str] = None
    social_accounts: List[SocialAccount] = []


class RiskItem(BaseModel):
    id: str
    category: str    # ACCOUNT, LOCATION, CONTACT, EXPOSURE, IDENTITY, OTHER
    severity: str    # HIGH, MEDIUM, LOW
    description: str
    suggested_action: str


class EmailExposureResult(BaseModel):
    email: str
    breach_found: bool = False
    breach_count: int = 0
    breach_sources: List[str] = []
    github_commits: Optional[int] = None
    keybase_found: Optional[bool] = None


class AnalyzeResponse(BaseModel):
    session_id: str
    privacy_score: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    risks: List[RiskItem]
    privacy_level: str          # "GÜÇLÜ" / "ORTA" / "ZAYIF"
    summary: str                # kısa TR açıklama
    email_exposure: Optional[EmailExposureResult] = None


# ======================================================
#  Health check
# ======================================================
@app.get("/health")
def health_check():
    return {"status": "ok"}


# ======================================================
#  Ana analiz fonksiyonu
# ======================================================
def calculate_privacy_score_and_risks(payload: AnalyzeRequest) -> AnalyzeResponse:
    risks: List[RiskItem] = []
    score = 100

    primary_email = payload.primary_email.strip().lower()

    # -------------------------------------------------
    # 1) Ana e-postada yıl / telefon / generic riskleri
    # -------------------------------------------------
    if email_contains_4digit_year(primary_email) or email_contains_2digit_year(primary_email):
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="ACCOUNT",
                severity="MEDIUM",
                description="Ana e-posta adresinin içinde muhtemelen doğum yılın yer alıyor.",
                suggested_action="Doğum yılı içermeyen, daha anonim bir e-posta adresi kullanmayı düşünebilirsin.",
            )
        )
        score -= 10

    if email_looks_like_phone(primary_email):
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="CONTACT",
                severity="HIGH",
                description="Ana e-posta adresin telefon numarasına çok benziyor.",
                suggested_action="E-posta adresinde doğrudan telefon numarası kullanmak yerine daha anonim bir kombinasyon tercih et.",
            )
        )
        score -= 25

    if email_local_too_generic(primary_email):
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="ACCOUNT",
                severity="LOW",
                description="Ana e-posta adresinin kullanıcı adı kısmı çok kısa veya çok genel görünüyor.",
                suggested_action="Tahmin edilmesi zor, sana özgü bir kullanıcı adı belirlemeyi düşünebilirsin.",
            )
        )
        score -= 5

    # E-posta içinde plaka / konum ipucu
    if text_has_location(primary_email):
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="LOCATION",
                severity="LOW",
                description="E-posta adresinde il / ilçe / plaka kodu gibi konumla ilişkilendirilebilecek sayılar veya ifadeler yer alıyor.",
                suggested_action="E-posta adresinde il/ilçe adı veya plaka kodu kullanmak, yaşadığın yerin tahmin edilebilirliğini artırabilir. Daha nötr kombinasyonlar tercih edebilirsin.",
            )
        )
        score -= 5

    # -------------------------------------------------
    # 2) Aynı ana e-posta kaç platformda kullanılıyor?
    # -------------------------------------------------
    platforms_using_primary_email = [
        acc.platform
        for acc in payload.social_accounts
        if acc.email and acc.email.strip().lower() == primary_email
    ]
    if len(platforms_using_primary_email) >= 3:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="ACCOUNT",
                severity="MEDIUM",
                description=f"Ana e-posta {len(platforms_using_primary_email)} farklı platformda kullanılıyor.",
                suggested_action="Kritik hesaplar (banka, kurumsal mail vb.) için farklı e-posta adresleri kullanmayı düşünebilirsin.",
            )
        )
        score -= 15

    # -------------------------------------------------
    # 3) Hesap bazlı telefon / konum / adres / kurum riskleri
    # -------------------------------------------------
    phone_risky_accounts: List[SocialAccount] = []
    location_risky_accounts: List[SocialAccount] = []
    address_risky_accounts: List[SocialAccount] = []
    org_risky_accounts: List[SocialAccount] = []

    for acc in payload.social_accounts:
        acc_email = (acc.email or "").strip().lower()
        combined_for_location = " ".join(
            [
                acc.username or "",
                acc.bio_text or "",
                acc_email,
            ]
        )

        # E-posta telefona benziyor mu?
        if acc_email and email_looks_like_phone(acc_email):
            phone_risky_accounts.append(acc)

        # Konum: checkbox veya metin içeriği (username + bio + email üzerinden)
        if acc.has_location_in_bio or text_has_location(combined_for_location):
            location_risky_accounts.append(acc)

        # Adres benzeri metin (bio üzerinden)
        if text_looks_like_address(acc.bio_text):
            address_risky_accounts.append(acc)

        # Kurum/okul/banka ipucu (username + bio)
        combined_org = " ".join(
            [
                acc.username or "",
                acc.bio_text or "",
            ]
        )
        if text_has_org_hint(combined_org):
            org_risky_accounts.append(acc)

    if phone_risky_accounts:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="CONTACT",
                severity="HIGH",
                description=f"{len(phone_risky_accounts)} hesapta kullanılan e-posta adresi telefon numarasına benziyor.",
                suggested_action="E-postalarda direkt telefon numarası kullanmak yerine daha anonim kullanıcı adları tercih et.",
            )
        )
        score -= 20

    if location_risky_accounts:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="LOCATION",
                severity="MEDIUM",
                description=f"{len(location_risky_accounts)} hesapta şehir / ilçe / plaka kodu gibi konum bilgisinin açık olduğu görülüyor.",
                suggested_action="Herkese açık profillerde ilçe, mahalle, plaka gibi detayları paylaşmamaya çalış.",
            )
        )
        score -= 15

    if address_risky_accounts:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="LOCATION",
                severity="HIGH",
                description=f"{len(address_risky_accounts)} hesapta mahalle / sokak / kapı numarası gibi adres bilgisinin paylaşılmış olma ihtimali yüksek.",
                suggested_action="Tam adres bilgini sadece zorunlu durumlarda, tercihen kapalı ve güvenli kanallardan paylaşmaya çalış.",
            )
        )
        score -= 25

    if org_risky_accounts:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="IDENTITY",
                severity="MEDIUM",
                description=f"{len(org_risky_accounts)} hesapta okul / kurum / banka gibi kurumsal bilgiler yer alıyor.",
                suggested_action="Okul / işyeri / banka gibi kurum bilgilerini birden fazla yerde aynı anda paylaşmak kimliğinin izlenebilirliğini artırır. Daha sınırlı paylaşmayı düşünebilirsin.",
            )
        )
        score -= 10

    # -------------------------------------------------
    # 4) Kurumsal e-posta kullanımı
    # -------------------------------------------------
    corporate_risky_accounts: List[SocialAccount] = []
    corporate_social_domains: set = set()

    primary_is_corp = is_corporate_email(primary_email)

    for acc in payload.social_accounts:
        acc_email = (acc.email or "").strip().lower()
        if not acc_email:
            continue
        if is_corporate_email(acc_email):
            if norm(acc.platform) in {
                "instagram", "x", "tiktok", "facebook", "reddit",
                "youtube", "discord", "other"
            }:
                corporate_risky_accounts.append(acc)
                _, dom = split_email(acc_email)
                corporate_social_domains.add(dom)

    if primary_is_corp and platforms_using_primary_email:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="ACCOUNT",
                severity="HIGH",
                description="Kurumsal e-posta adresin sosyal platformlarda da kullanılıyor.",
                suggested_action="İş e-posta adresini sadece iş amaçlı kanallarda kullanmaya, sosyal platformlarda kişisel e-posta açmaya çalış.",
            )
        )
        score -= 25

    if corporate_risky_accounts:
        dom_list = ", ".join(sorted(corporate_social_domains))
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="ACCOUNT",
                severity="MEDIUM",
                description=f"Sosyal platformlarda kurumsal e-posta uzantısı kullanıyorsun ({dom_list}).",
                suggested_action="Kurumsal e-posta, iş ve güvenlik politikaları açısından sosyal medya için uygun olmayabilir; kişisel bir adres kullanman daha güvenli olur.",
            )
        )
        score -= 15

    # -------------------------------------------------
    # 5) Kullanıcı adı – gerçek isim benzerliği & aynı username
    # -------------------------------------------------
    name_tokens = normalize_name_tokens(payload.full_name)
    username_like_realname_count = 0

    username_to_platforms: Dict[str, set] = {}

    for acc in payload.social_accounts:
        uname = norm(acc.username or "")
        if not uname:
            continue

        # aynı username kaç platformda?
        username_to_platforms.setdefault(uname, set()).add(acc.platform)

        # gerçek isim token'ları username içinde geçiyor mu?
        if any(tok in uname for tok in name_tokens):
            username_like_realname_count += 1

    # username = gerçek isim benzeri hesaplar fazlaysa
    if username_like_realname_count >= 2 and name_tokens:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="IDENTITY",
                severity="MEDIUM",
                description="Birden fazla hesapta kullanıcı adın gerçek isminle çok benzer.",
                suggested_action="Takma ad kullanmak veya en azından bazı hesaplarda gerçek ismine çok yakın olmayan kullanıcı adları tercih etmek izlenebilirliğini azaltır.",
            )
        )
        score -= 10

    # aynı username 3+ platformda kullanılıyorsa
    shared_usernames = [
        (uname, plats)
        for uname, plats in username_to_platforms.items()
        if len(plats) >= 3
    ]
    if shared_usernames:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="EXPOSURE",
                severity="MEDIUM",
                description="Aynı kullanıcı adını 3 veya daha fazla platformda kullanıyorsun.",
                suggested_action="Her yerde aynı kullanıcı adını kullanmak, seni platformlar arasında takip etmeyi kolaylaştırır. Kritik hesaplarda farklı kullanıcı adları tercih etmeyi düşünebilirsin.",
            )
        )
        score -= 10

    # -------------------------------------------------
    # 6) Dijital görünürlük: hesap sayısı & public hesaplar
    # -------------------------------------------------
    total_accounts = len(payload.social_accounts)
    public_accounts = sum(1 for a in payload.social_accounts if a.is_public)

    if total_accounts >= 5:
        sev = "MEDIUM" if total_accounts < 8 else "HIGH"
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="EXPOSURE",
                severity=sev,
                description=f"Sisteme {total_accounts} adet sosyal / dijital hesap girişi yaptın.",
                suggested_action="Aktif kullanmadığın hesapları kapatmak veya en azından gizli hale getirmek saldırı yüzeyini daraltır.",
            )
        )
        score -= 10 if sev == "MEDIUM" else 15

    if public_accounts >= 3:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="EXPOSURE",
                severity="MEDIUM",
                description=f"{public_accounts} hesabın herkese açık durumda.",
                suggested_action="Özellikle kişisel bilgilerin bulunduğu profilleri gizli yapmayı veya paylaşılan bilgileri minimumda tutmayı düşünebilirsin.",
            )
        )
        score -= 10

    # -------------------------------------------------
    # 7) Email exposure analizi (breach / GitHub / Keybase)
    # -------------------------------------------------
    breach_found, breach_sources = check_breaches_for_email(primary_email)
    github_commits = github_commit_count_for_email(primary_email)
    keybase_found = keybase_has_profile_for_email(primary_email)

    email_exposure = EmailExposureResult(
        email=primary_email,
        breach_found=breach_found,
        breach_count=len(breach_sources) if breach_found else 0,
        breach_sources=breach_sources,
        github_commits=github_commits,
        keybase_found=keybase_found,
    )

    if breach_found:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="ACCOUNT",
                severity="HIGH",
                description="Ana e-posta adresin büyük veri sızıntılarında (data breach) yer almış görünüyor.",
                suggested_action="Bu e-posta ile ilişkili tüm hesaplarda parolayı yenilemen, mümkünse 2FA açman ve kritik yerlerde farklı e-posta/parola kombinasyonları kullanman önerilir.",
            )
        )
        score -= 30

    if github_commits is not None and github_commits > 0 and is_corporate_email(primary_email):
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="ACCOUNT",
                severity="MEDIUM",
                description="Kurumsal e-posta adresin GitHub commit geçmişinde görünüyor.",
                suggested_action="İş e-posta adresini açık kaynak veya public projelerde kullanmak yerine kişisel bir e-posta tercih etmen daha güvenli olur.",
            )
        )
        score -= 10

    if keybase_found is True:
        risks.append(
            RiskItem(
                id=str(uuid.uuid4()),
                category="EXPOSURE",
                severity="LOW",
                description="E-posta adresin Keybase üzerinde bir profil ile ilişkilendirilmiş.",
                suggested_action="Bu durum tek başına risk değil, ancak farklı platformlarda aynı e-postayı kullanmanın seni izlenebilir kıldığını unutma.",
            )
        )
        score -= 5

    # -------------------------------------------------
    # 8) Skor, seviye ve özet
    # -------------------------------------------------
    score = max(0, min(100, score))

    high_count = sum(1 for r in risks if r.severity == "HIGH")
    med_count = sum(1 for r in risks if r.severity == "MEDIUM")
    low_count = sum(1 for r in risks if r.severity == "LOW")

    if score >= 80:
        privacy_level = "GÜÇLÜ"
    elif score >= 50:
        privacy_level = "ORTA"
    else:
        privacy_level = "ZAYIF"

    # En ağır kategorileri bul (HIGH -> MEDIUM)
    main_cats: List[str] = []
    for sev in ("HIGH", "MEDIUM"):
        for r in risks:
            if r.severity == sev and r.category not in main_cats:
                main_cats.append(r.category)
    main_cats = main_cats[:2]

    cat_desc_map = {
        "ACCOUNT": "e-posta ve hesap yapısı",
        "CONTACT": "iletişim bilgileri",
        "LOCATION": "konum / adres paylaşımı",
        "EXPOSURE": "dijital görünürlük",
        "IDENTITY": "kimlik / kurum bilgileri",
        "OTHER": "diğer alanlar",
    }

    if not risks:
        summary = "Genel gizlilik seviyen oldukça güçlü görünüyor. Yine de zaman zaman paylaştığın bilgileri gözden geçirmen faydalı olur."
    else:
        if main_cats:
            katlar = [cat_desc_map.get(c, c.lower()) for c in main_cats]
            if len(katlar) == 1:
                kat_text = katlar[0]
            else:
                kat_text = f"{katlar[0]} ve {katlar[1]}"
            summary = (
                f"Genel gizlilik seviyen {privacy_level}. "
                f"Özellikle {kat_text} konusunda daha dikkatli olman faydalı olur."
            )
        else:
            summary = (
                f"Genel gizlilik seviyen {privacy_level}. "
                "Bazı alanlarda iyileştirme yapman önerilir."
            )

    return AnalyzeResponse(
        session_id=str(uuid.uuid4()),
        privacy_score=score,
        high_risk_count=high_count,
        medium_risk_count=med_count,
        low_risk_count=low_count,
        risks=risks,
        privacy_level=privacy_level,
        summary=summary,
        email_exposure=email_exposure,
    )


# ======================================================
#  API endpoint
# ======================================================
@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest):
    return calculate_privacy_score_and_risks(payload)

