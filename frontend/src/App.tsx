import { useState, FormEvent } from "react";


const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type RiskItem = {
  id: string;
  category: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  description: string;
  suggested_action: string;
};

type EmailExposure = {
  email: string;
  breach_found: boolean;
  breach_count: number;
  breach_sources: string[];
  github_commits: number | null;
  keybase_found: boolean | null;
};

type AnalyzeResponse = {
  session_id: string;
  privacy_score: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
  risks: RiskItem[];
  privacy_level: string;
  summary: string;
  email_exposure?: EmailExposure;
};

type SocialForm = {
  platform: string;
  username: string;
  email: string;
  is_public: boolean;
  has_phone_in_bio: boolean;
  has_location_in_bio: boolean;
  bio_text: string;
};

function severityBadge(severity: RiskItem["severity"]) {
  const base =
    "inline-flex items-center rounded-full px-2 py-0.5 text-[0.7rem] font-medium";
  if (severity === "HIGH") {
    return (
      <span
        className={`${base} bg-red-500/20 text-red-300 border border-red-500/40`}
      >
        YÜKSEK
      </span>
    );
  }
  if (severity === "MEDIUM") {
    return (
      <span
        className={`${base} bg-amber-500/20 text-amber-300 border border-amber-500/40`}
      >
        ORTA
      </span>
    );
  }
  return (
    <span
      className={`${base} bg-emerald-500/20 text-emerald-300 border border-emerald-500/40`}
    >
      DÜŞÜK
    </span>
  );
}

function categoryLabel(cat: string) {
  const map: Record<string, string> = {
    ACCOUNT: "Hesap / E-posta",
    LOCATION: "Konum",
    CONTACT: "İletişim",
    EXPOSURE: "Dijital Görünürlük",
    IDENTITY: "Kimlik / Kurum",
    OTHER: "Diğer",
  };
  return map[cat] ?? cat;
}

function App() {
  const [fullName, setFullName] = useState("");
  const [primaryEmail, setPrimaryEmail] = useState("");

  const [accounts, setAccounts] = useState<SocialForm[]>([
    {
      platform: "instagram",
      username: "",
      email: "",
      is_public: true,
      has_phone_in_bio: false,
      has_location_in_bio: false,
      bio_text: "",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAccountChange = (
    index: number,
    field: keyof SocialForm,
    value: string | boolean
  ) => {
    setAccounts((prev) =>
      prev.map((acc, i) =>
        i === index ? { ...acc, [field]: value } : acc
      )
    );
  };

  const addAccount = () => {
    setAccounts((prev) => [
      ...prev,
      {
        platform: "instagram",
        username: "",
        email: "",
        is_public: true,
        has_phone_in_bio: false,
        has_location_in_bio: false,
        bio_text: "",
      },
    ]);
  };

  const removeAccount = (index: number) => {
    setAccounts((prev) =>
      prev.length <= 1 ? prev : prev.filter((_, i) => i !== index)
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setData(null);

    try {
      const payload = {
        full_name: fullName,
        primary_email: primaryEmail,
        social_accounts: accounts,
      };

      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const json = (await res.json()) as AnalyzeResponse;
      setData(json);
    } catch (err: any) {
      setError(err.message ?? "Bilinmeyen hata");
    } finally {
      setLoading(false);
    }
  };

  const score = data?.privacy_score ?? 0;
  const scoreColor =
    score >= 80
      ? "from-emerald-500 to-emerald-400"
      : score >= 50
      ? "from-amber-500 to-amber-400"
      : "from-red-500 to-rose-500";

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900">
      <div className="mx-auto max-w-6xl px-4 py-8">
        {/* HEADER */}
        <header className="pb-6 border-b border-slate-800 text-center">
          <h1 className="text-3xl font-semibold tracking-tight text-slate-50">
            Personal Data Guardian
          </h1>
          <p className="mt-1 text-sm text-slate-400 max-w-xl mx-auto">
            Dijital ayak izin üzerinden{" "}
            <span className="text-slate-200 font-medium">
              gizlilik skorunu ve risklerini
            </span>{" "}
            hesaplayan, herkesin kendi verisiyle gerçek zamanlı
            kullanabileceği bir araç.
          </p>
        </header>

        <main className="mt-6 space-y-6">
          {/* FORM */}
          <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-black/40">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium text-slate-200">
                Profil Bilgileri
              </h2>
              <button
                type="button"
                onClick={addAccount}
                className="text-xs rounded-lg bg-slate-800 px-3 py-1.5 border border-slate-700 hover:border-sky-500 text-slate-200"
              >
                + Hesap Ekle
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-300">Ad Soyad</label>
                  <input
                    className="w-full mt-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-sky-500 outline-none"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Ad Soyad"
                  />
                </div>
                <div>
                  <label className="text-xs text-slate-300">
                    Ana E-posta
                  </label>
                  <input
                    className="w-full mt-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-sky-500 outline-none"
                    value={primaryEmail}
                    onChange={(e) => setPrimaryEmail(e.target.value)}
                    placeholder="ornek@example.com"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <h3 className="text-xs text-slate-400 font-semibold">
                  Sosyal Hesaplar
                </h3>

                {accounts.map((acc, index) => (
                  <div
                    key={index}
                    className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[0.7rem] text-slate-400">
                        Hesap #{index + 1}
                      </span>
                      <button
                        type="button"
                        disabled={accounts.length <= 1}
                        onClick={() => removeAccount(index)}
                        className="text-[0.65rem] text-red-400 hover:text-red-300 disabled:opacity-50"
                      >
                        Sil
                      </button>
                    </div>

                    <div className="grid md:grid-cols-3 gap-2">
                      <div>
                        <label className="text-[0.7rem] text-slate-400">
                          Platform
                        </label>
                        <select
                          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-100"
                          value={acc.platform}
                          onChange={(e) =>
                            handleAccountChange(
                              index,
                              "platform",
                              e.target.value
                            )
                          }
                        >
                          <option value="instagram">Instagram</option>
                          <option value="linkedin">LinkedIn</option>
                          <option value="github">GitHub</option>
                          <option value="x">X (Twitter)</option>
                          <option value="tiktok">TikTok</option>
                          <option value="facebook">Facebook</option>
                          <option value="other">Diğer</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-[0.7rem] text-slate-400">
                          Kullanıcı Adı
                        </label>
                        <input
                          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-100"
                          value={acc.username}
                          onChange={(e) =>
                            handleAccountChange(
                              index,
                              "username",
                              e.target.value
                            )
                          }
                          placeholder="kullanici_adi"
                        />
                      </div>

                      <div>
                        <label className="text-[0.7rem] text-slate-400">
                          Bu hesapta kullanılan e-posta
                        </label>
                        <input
                          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-100"
                          value={acc.email}
                          onChange={(e) =>
                            handleAccountChange(
                              index,
                              "email",
                              e.target.value
                            )
                          }
                          placeholder="ornek@example.com"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-[0.7rem] text-slate-400 block">
                        Profil bio / açıklama (opsiyonel)
                      </label>
                      <textarea
                        className="w-full rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-100 min-h-[50px]"
                        value={acc.bio_text}
                        onChange={(e) =>
                          handleAccountChange(
                            index,
                            "bio_text",
                            e.target.value
                          )
                        }
                        placeholder="Örn: Şehir · İlçe · İlgi alanı"
                      />
                    </div>

                    <div className="flex flex-wrap gap-4">
                      <label className="flex items-center gap-2 text-[0.7rem] text-slate-400">
                        <input
                          type="checkbox"
                          checked={acc.is_public}
                          onChange={(e) =>
                            handleAccountChange(
                              index,
                              "is_public",
                              e.target.checked
                            )
                          }
                          className="h-3.5 w-3.5 rounded border-slate-700 bg-slate-900"
                        />
                        Profil herkese açık
                      </label>
                      <label className="flex items-center gap-2 text-[0.7rem] text-slate-400">
                        <input
                          type="checkbox"
                          checked={acc.has_phone_in_bio}
                          onChange={(e) =>
                            handleAccountChange(
                              index,
                              "has_phone_in_bio",
                              e.target.checked
                            )
                          }
                          className="h-3.5 w-3.5 rounded border-slate-700 bg-slate-900"
                        />
                        Bio&apos;da telefon geçiyor
                      </label>
                      <label className="flex items-center gap-2 text-[0.7rem] text-slate-400">
                        <input
                          type="checkbox"
                          checked={acc.has_location_in_bio}
                          onChange={(e) =>
                            handleAccountChange(
                              index,
                              "has_location_in_bio",
                              e.target.checked
                            )
                          }
                          className="h-3.5 w-3.5 rounded border-slate-700 bg-slate-900"
                        />
                        Bio&apos;da konum geçiyor
                      </label>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-between pt-2">
                {error && (
                  <span className="text-xs text-red-400">
                    Hata: {error}
                  </span>
                )}
                <button
                  type="submit"
                  disabled={loading}
                  className="ml-auto inline-flex items-center rounded-lg bg-sky-500 px-4 py-2 text-xs font-medium text-white hover:bg-sky-400 disabled:opacity-60"
                >
                  {loading ? "Analiz ediliyor..." : "Analiz Et"}
                </button>
              </div>
            </form>
          </section>

  
          <section className="grid gap-6 md:grid-cols-[minmax(0,1.1fr)_minmax(0,1.6fr)]">
 
            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 text-center shadow-xl shadow-black/40">
              <h2 className="text-sm font-medium text-slate-200 mb-3">
                Gizlilik Skoru
              </h2>
              {loading ? (
                <p className="text-slate-400 text-sm">Analiz ediliyor...</p>
              ) : !data ? (
                <p className="text-slate-500 text-xs">
                  Henüz analiz yapılmadı. Formu doldurup{" "}
                  <span className="font-semibold text-slate-300">
                    Analiz Et
                  </span>{" "}
                  butonuna tıkla.
                </p>
              ) : (
                <div className="flex flex-col items-center">
                  <div
                    className={`h-40 w-40 rounded-full bg-gradient-to-tr ${scoreColor} p-[3px] flex items-center justify-center`}
                  >
                    <div className="bg-slate-950 rounded-full h-full w-full flex flex-col items-center justify-center">
                      <span className="text-4xl font-bold">{score}</span>
                      <span className="text-xs text-slate-400">/100</span>
                    </div>
                  </div>
                  <span className="mt-3 inline-flex items-center rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-[0.7rem] font-medium text-slate-100">
                    Genel gizlilik seviyen:{" "}
                    <span className="ml-1 text-sky-400">
                      {data.privacy_level}
                    </span>
                  </span>
                  <p className="mt-2 text-xs text-slate-400 max-w-xs mx-auto">
                    {data.summary}
                  </p>
                </div>
              )}
            </div>

            {/* Riskler */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-black/40">
              <h2 className="text-sm font-medium text-slate-200 mb-3">
                Tespit Edilen Riskler
              </h2>
              {loading ? (
                <p className="text-slate-400 text-sm">
                  Riskler yükleniyor...
                </p>
              ) : !data || data.risks.length === 0 ? (
                <p className="text-slate-500 text-xs">
                  Henüz risk listesi yok. Analiz sonrası burada detaylı
                  risk maddeleri görünecek.
                </p>
              ) : (
                <div className="space-y-3 max-h-[360px] overflow-y-auto">
                  {data.risks.map((r) => (
                    <div
                      key={r.id}
                      className="rounded-xl border border-slate-800 bg-slate-900/90 p-3 hover:border-slate-700 transition"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          {severityBadge(r.severity)}
                          <span className="text-xs text-slate-400">
                            {categoryLabel(r.category)}
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-slate-200">
                        {r.description}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        <span className="text-slate-300 font-semibold">
                          Öneri:
                        </span>{" "}
                        {r.suggested_action}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

   
          <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-xl shadow-black/40">
            <h2 className="text-sm font-medium text-slate-200 mb-2">
              E-posta Dijital İzi Analizi
            </h2>
            {!data || !data.email_exposure ? (
              <p className="text-xs text-slate-500">
                Analiz sonrasında ana e-posta adresinin sızıntı ve görünürlük
                izleri burada özetlenecek.
              </p>
            ) : (
              <div className="grid gap-4 md:grid-cols-3 text-xs">
     
                <div className="space-y-1">
                  <p className="text-slate-400">
                    Analiz edilen e-posta:{" "}
                    <span className="text-slate-200 font-medium">
                      {data.email_exposure.email}
                    </span>
                  </p>
                  <p className="text-slate-400">
                    Sızıntı kaynağı tespit edildi mi?{" "}
                    <span className="font-semibold">
                      {data.email_exposure.breach_found
                        ? "Evet"
                        : "Hayır / Bilgi yok"}
                    </span>
                  </p>
                  {data.email_exposure.breach_found &&
                    data.email_exposure.breach_sources.length > 0 && (
                      <p className="text-slate-400">
                        Öne çıkan kaynaklar:{" "}
                        <span className="text-slate-200">
                          {data.email_exposure.breach_sources.join(", ")}
                        </span>
                      </p>
                    )}
                </div>

 
                <div className="space-y-1">
                  <p className="text-slate-400 font-semibold mb-1">
                    GitHub İzleri
                  </p>
                  {data.email_exposure.github_commits == null ? (
                    <p className="text-slate-500">
                      GitHub için otomatik sorgu yapılmadı veya yanıt alınamadı.
                    </p>
                  ) : data.email_exposure.github_commits === 0 ? (
                    <p className="text-slate-400">
                      Bu e-posta ile ilişkili public commit bulunmadı.
                    </p>
                  ) : (
                    <p className="text-slate-400">
                      Bu e-posta ile ilişkili yaklaşık{" "}
                      <span className="font-semibold text-slate-200">
                        {data.email_exposure.github_commits}
                      </span>{" "}
                      adet public commit kaydı görünüyor.
                    </p>
                  )}
                </div>

       
                <div className="space-y-1">
                  <p className="text-slate-400 font-semibold mb-1">
                    Diğer İzler
                  </p>
                  {data.email_exposure.keybase_found == null ? (
                    <p className="text-slate-500">
                      Keybase kontrolü sırasında bilgi alınamadı.
                    </p>
                  ) : data.email_exposure.keybase_found ? (
                    <p className="text-slate-400">
                      E-posta, Keybase üzerinde bir profil ile eşleşiyor. Bu
                      durum kimlik doğrulama açısından güçlü bir bağ oluştururken
                      izlenebilirlik açısından da görünürlüğünü artırabilir.
                    </p>
                  ) : (
                    <p className="text-slate-400">
                      E-posta için Keybase üzerinde bir profil bulunamadı.
                    </p>
                  )}
                </div>
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

export default App;

