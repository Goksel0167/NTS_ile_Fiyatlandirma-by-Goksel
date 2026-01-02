import 'package:flutter/material.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  // --- DEĞİŞKENLER (State) ---
  String? selectedProduct;
  String selectedCurrency = 'EUR'; // Varsayılan Euro olsun
  double profitMargin = 15.0; // Varsayılan Marj %15
  String? selectedDestination;
  
  // Örnek Veriler (Veritabanından gelecek)
  final List<String> products = [
    'Sika Viscocrete HT 2541',
    'Sika Viscocrete PC 61',
    'Sikament 524 RMC'
  ];
  
  final List<String> cities = ['DIYARBAKIR', 'BATMAN', 'MARDIN', 'TRABZON'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text('NTS Mobil', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
        backgroundColor: const Color(0xFFD32F2F), // Sika Kırmızısı
        centerTitle: true,
        elevation: 0,
        actions: [
          IconButton(onPressed: () {}, icon: const Icon(Icons.refresh, color: Colors.white)) // Kurları yenile
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // --- 1. KART: ÜRÜN VE MALİYET ---
            _buildSectionTitle('Ürün Maliyet Girişi'),
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    // Ürün Seçimi
                    DropdownButtonFormField<String>(
                      decoration: const InputDecoration(
                        labelText: 'Ürün Seçiniz',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.layers),
                      ),
                      value: selectedProduct,
                      items: products.map((String value) {
                        return DropdownMenuItem<String>(value: value, child: Text(value));
                      }).toList(),
                      onChanged: (val) => setState(() => selectedProduct = val),
                    ),
                    const SizedBox(height: 16),
                    
                    // Maliyet Girişi ve Para Birimi (Yan Yana)
                    Row(
                      children: [
                        Expanded(
                          flex: 2,
                          child: TextFormField(
                            keyboardType: const TextInputType.numberWithOptions(decimal: true),
                            decoration: const InputDecoration(
                              labelText: 'Maliyet (KG)',
                              hintText: '2.50',
                              border: OutlineInputBorder(),
                              suffixText: 'Birim',
                            ),
                          ),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          flex: 3,
                          child: _buildCurrencySelector(),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // --- 2. KART: LOJİSTİK VE ROTA ---
            _buildSectionTitle('Lojistik Planlama'),
            Card(
              elevation: 4,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  children: [
                    // Varış Yeri Seçimi
                    DropdownButtonFormField<String>(
                      decoration: const InputDecoration(
                        labelText: 'Varış Noktası',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.local_shipping),
                      ),
                      value: selectedDestination,
                      items: cities.map((String value) {
                        return DropdownMenuItem<String>(value: value, child: Text(value));
                      }).toList(),
                      onChanged: (val) => setState(() => selectedDestination = val),
                    ),
                    const SizedBox(height: 12),
                    // Nakliye Seçim Butonu (Henüz boş)
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: () {
                          // TODO: Nakliye Seçim Ekranını Aç
                        },
                        icon: const Icon(Icons.search),
                        label: const Text('Nakliye Firmalarını Getir (Baykan/Çalışkan)'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blueGrey[800],
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 20),

            // --- 3. KART: KÂRLILIK AYARI ---
            _buildSectionTitle('Kâr Marjı: %${profitMargin.toInt()}'),
            Card(
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 10),
                child: Slider(
                  value: profitMargin,
                  min: 0,
                  max: 50,
                  divisions: 50,
                  label: '%${profitMargin.toInt()}',
                  activeColor: const Color(0xFFD32F2F),
                  onChanged: (double value) {
                    setState(() {
                      profitMargin = value;
                    });
                  },
                ),
              ),
            ),

            const SizedBox(height: 30),

            // --- HESAPLA BUTONU ---
            SizedBox(
              height: 55,
              child: ElevatedButton(
                onPressed: () {
                   // TODO: Sonuç Ekranına Git
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFD32F2F),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  elevation: 5,
                ),
                child: const Text(
                  'HESAPLA VE SONUÇLARI GÖSTER',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // Yardımcı Widget: Başlıklar
  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 8.0, bottom: 8.0),
      child: Text(
        title,
        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.grey[800]),
      ),
    );
  }

  // Yardımcı Widget: Para Birimi Seçici (Toggle)
  Widget _buildCurrencySelector() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey.shade400)
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: ['TL', 'USD', 'EUR', 'CHF'].map((currency) {
          bool isSelected = selectedCurrency == currency;
          return GestureDetector(
            onTap: () => setState(() => selectedCurrency = currency),
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
              decoration: BoxDecoration(
                color: isSelected ? Colors.blueGrey[800] : Colors.transparent,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                currency,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                  color: isSelected ? Colors.white : Colors.black87,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}