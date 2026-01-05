# 🚛 NTS & Lojistik Maliyet Analiz Sistemi

Bu proje, **Hazır Beton ve Yapı Kimyasalları** sektöründeki sevkiyat süreçlerini, NTS (Net Fabrika Teslim) maliyetlerini ve nakliye giderlerini optimize etmek için geliştirilmiş bir **Python/Streamlit** web uygulamasıdır.

## 🎯 Projenin Amacı

Bölge yöneticilerinin ve lojistik sorumlularının;
* 3 farklı fabrika (TR14-Gebze, TR15-Trabzon, TR16-Adana) arasından en uygun üretim noktasını bulmasını,
* Tüm nakliye firmaları (Baykan, Çalışkan) ve araç tiplerini (Tır, Kırkayak) karşılaştırmasını,
* Ürün maliyetlerinin tarihsel geçmişini takip etmesini,
* Otomatik olarak en ucuz rota+fabrika kombinasyonunu hesaplamasını sağlar.



## 🚀 Özellikler

* **Akıllı Fiyat Karşılaştırma:** Aynı ürün için 3 fabrika + 2 nakliye firması kombinasyonlarını otomatik hesaplar ve en ucuzunu gösterir.
* **Tarihsel Fiyat Takibi:** Ürün maliyetlerinin zaman içindeki değişimini kayıt altına alır, en güncel fiyatı hesaplamada kullanır.
* **Çoklu Döviz Desteği:** TL, USD, EUR, CHF cinsinden anlık satış fiyatı gösterir.
* **Esnek Kâr Marjı:** %0-100 arası ayarlanabilir, varsayılan %30.
* **Yeni Ürün Ekleme:** UI üzerinden tarih damgalı yeni NTS maliyetleri eklenebilir.
* **Lojistik Yönetimi:** Nakliye fiyatlarına toplu zam veya tek tek düzenleme yapılabilir.
* **Mobil Uyumlu:** Streamlit Cloud üzerinden telefon ve tabletlerden erişilebilir.



\## 🛠 Kullanılan Teknolojiler



\* \*\*Python 3.13\*\*

\* \*\*Streamlit\*\* (Web Arayüzü)

\* \*\*Pandas\*\* (Veri Analizi ve Tablolama)



\## 💻 Kurulum ve Çalıştırma (Lokal)



Bu projeyi kendi bilgisayarınızda geliştirmek isterseniz:



1\.  Repoyu klonlayın:

&nbsp;   ```bash

&nbsp;   git clone \[https://github.com/Goksel0167/NTS\_Proje.git](https://github.com/Goksel0167/NTS\_Proje.git)

&nbsp;   ```

2\.  Gerekli kütüphaneleri yükleyin:

&nbsp;   ```bash

&nbsp;   pip install -r requirements.txt

&nbsp;   ```

3\.  Uygulamayı başlatın:

&nbsp;   ```bash

&nbsp;   streamlit run app.py

&nbsp;   ```



## 🌐 Canlı Kullanım

Uygulama Streamlit Cloud üzerinde 7/24 aktiftir:
**https://ntsilefiyatlandirma-by-goksel.streamlit.app/**



---

\*\*Geliştirici:\*\* Göksel Çapkın

