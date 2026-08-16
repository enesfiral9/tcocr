# T.C. Kimlik OCR

Kurum içi ağda, internet ve veritabanı olmadan çalışan FastAPI tabanlı T.C. kimlik kartı OCR sistemi. PDF/JPG/PNG belgeleri sunucuda işler; sonuçlar yalnızca işlem belleğinde ve tarayıcı state'inde kalır. Yüklenen dosyalar `finally` bloğunda silinir. Kalıcı kişisel veri çıktısı yalnızca kullanıcının indirdiği Excel dosyasıdır.

## Mimari ve işlem hattı

Tarayıcı → FastAPI → PyMuPDF (sayfa sayfa) → OpenCV kart tespiti → perspektif düzeltme → standart kart → alan kırpma → lokal PaddleOCR → normalization/validation → JSON → kullanıcı düzeltmesi → openpyxl.

Uygulama hiçbir bulut servisi, harici API, veritabanı veya browser OCR kitaplığı kullanmaz. Tek CPU-ağır tarama kilidi vardır; ikinci eşzamanlı istek HTTP 409 alır. PDF sayfalarının tamamı aynı anda belleğe alınmaz.

## Windows gereksinimleri ve kurulum

- 64-bit Windows 10/11 veya Windows Server, güncel CPU, büyük PDF'ler için en az 16 GB RAM önerilir.
- Python 3.10 veya 3.11 (64 bit) kurun ve kurulumda `Add Python to PATH` seçin.
- Projeyi örneğin `C:\IdentityOCR` altına kopyalayın.

PowerShell/CMD:

```bat
cd C:\IdentityOCR
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PaddlePaddle'ın Windows/CPU paket uygunluğu Python sürümüne göre değişebilir. Kurulumda hata olursa PaddlePaddle'ın kurum dışındaki hazırlık bilgisayarında seçilen Python sürümüne uygun CPU wheel'ini indirin; aynı wheel'i offline sunucuya taşıyıp `pip install dosya.whl` ile kurun. Ardından kalan paketleri yerel wheel klasöründen yüklemek için:

```bat
pip download -r requirements.txt -d wheels
pip install --no-index --find-links=wheels -r requirements.txt
```

İlk komut internet erişimli hazırlık bilgisayarında, ikinci komut offline sunucuda çalıştırılır. Python sürümü ve mimarisi iki bilgisayarda aynı olmalıdır.

## Offline PaddleOCR modelleri

Model indirme uygulama runtime'ında kesinlikle yapılmaz. Türkçe/Latin karakter destekli PaddleOCR 3.x detection ve recognition inference model klasörlerini önceden hazırlayıp şu yapıya yerleştirin:

```text
models/
├── detection/      # model.json/model.pdmodel ve model ağırlıkları
└── recognition/    # model.json/model.pdmodel, ağırlıklar ve sözlük varlıkları
```

Kurumunuz farklı bir konum kullanıyorsa `DET_MODEL_DIR`, `REC_MODEL_DIR` ve gerekirse `OCR_LANG=tr` ortam değişkenlerini ayarlayın. `/api/health` ancak iki klasör mevcut ve PaddleOCR başarıyla kurulmuşsa `ocr_ready: true` döner. Dağıtımdan önce sunucunun internetini kapatıp health ve örnek OCR testiyle doğrulayın.

## Çalıştırma ve ağ erişimi

`start.bat` dosyasına çift tıklayın veya:

```bat
venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Sunucuda `http://127.0.0.1:8000`, kurum bilgisayarlarında `http://SUNUCU_IP:8000` adresini açın. Windows Defender Firewall'da yalnızca kurum ağı profili ve mümkünse kurum subnet'i için TCP 8000 inbound kuralı oluşturun. Public profile'a açmayın. Sabit IP veya DHCP reservation kullanın.

## Ayarlar

Temel ayarlar `app/config.py` içindedir ve çoğu ortam değişkeniyle değiştirilebilir: `PDF_DPI=300`, `CARD_WIDTH=1000`, `CARD_HEIGHT=630`, `MAX_UPLOAD_SIZE_MB=500`, `DEBUG_OCR=false`. Alan oranları `FIELD_COORDINATES` sözlüğündedir.

## OCR debug ve koordinat kalibrasyonu

`DEBUG_OCR=true` yalnızca kontrollü test ortamında açılmalıdır. Her iş için `debug/<uuid>/page_001/` altında original, grayscale, edges, normalized card, alan kutuları ve alan crop'ları üretir. `card_with_fields.png` üzerinde kutuları kontrol edip `FIELD_COORDINATES` oranlarını ayarlayın. Debug görüntüleri kişisel veri içerebilir; production'da kapalı tutun ve test çıktısını manuel temizleyin. Normal temp dosyaları her işlem sonunda otomatik silinir.

Kartın ön/arka yüzü, eski/yeni kimlik baskısı, fotokopi ölçeği ve tarayıcı ayarları koordinatları etkiler. Canlı kullanımdan önce yalnızca kurumun yetkili, sentetik/test örnekleriyle farklı tarayıcı ve dönüş açılarını kapsayan kalibrasyon yapılmalıdır.

## Test ve CLI

Validator testleri gerçek kişisel veri içermez:

```bat
pytest -q
python test_ocr.py test_identity.jpg
```

CLI JSON çıktısı alan değerlerini, güvenleri, doğrulama ve hata bilgilerini içerir. Model olmadan validator testleri yine çalışır.

## Production ve otomatik başlatma

İlk sürüm için `start.bat` yeterlidir. Windows açılışında başlatmak için Task Scheduler'da yeni görev oluşturun: kullanıcı oturumundan bağımsız çalıştırın, `Program/script` olarak `C:\IdentityOCR\start.bat`, başlangıç klasörü olarak `C:\IdentityOCR` seçin; başarısızlıkta yeniden başlatmayı etkinleştirin. Servis hesabına yalnızca proje/temp/log klasörlerinde gerekli izinleri verin.

Uvicorn'u tek worker ile çalıştırın; birden fazla worker ayrı OCR modeli ve ayrı lock oluşturup RAM tüketimini ve eşzamanlılığı bozar. Kurum ağı dışında erişime açmayın. Reverse proxy kullanılıyorsa upload limitini 500 MB ile uyumlu ayarlayın.

## Offline kullanım kontrol listesi

- Wheel paketleri, Python ve model dosyaları offline sunucuya eksiksiz taşındı.
- Sunucu interneti kapalıyken `/api/health` hazır dönüyor ve sentetik OCR testi geçiyor.
- Tek worker, kurum-ağı firewall kuralı ve sabit sunucu IP'si yapılandırıldı.
- `DEBUG_OCR=false`; `temp/`, `debug/`, `output/` ve log izinleri sınırlandırıldı.
- Loglarda OCR metni, ad, T.C. no, doğum tarihi veya seri no bulunmadığı doğrulandı.
- Tarama sonrası job klasörünün silindiği hata senaryolarında da test edildi.
- Model lisansları ve kurumun kişisel veri saklama politikası hukuk/bilgi güvenliği ekiplerince onaylandı.

## API

- `GET /api/health`: OCR hazırlık durumu
- `POST /api/scan`: multipart `file`; PDF/JPG/JPEG/PNG
- `POST /api/export`: tarayıcıdaki düzenlenmiş kayıtları Excel'e dönüştürür

API dokümantasyonu kurum içinde `/docs` adresindedir. Uygulama yeniden başladığında bütün RAM verileri kaybolur; bu tasarım gereğidir.
