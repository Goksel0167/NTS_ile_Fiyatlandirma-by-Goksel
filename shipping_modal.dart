import 'package:flutter/material.dart';

// Basit veri modeli (Normalde veritabanından gelecek)
class ShippingOption {
  final String companyName; // Baykan / Çalışkan
  final String vehicleType; // Tır / Kırkayak
  final double pricePerKg;  // 2.69 TL
  final String routeCode;   // TR16 vs.
  final bool isCheapest;    // En ucuz bu mu?

  ShippingOption(this.companyName, this.vehicleType, this.pricePerKg, this.routeCode, {this.isCheapest = false});
}

// Bu fonksiyonu Dashboard ekranındaki butona bağlayacağız
void showShippingSelector(BuildContext context, String destination, Function(ShippingOption) onSelected) {
  
  // SİMÜLASYON VERİSİ: Diyarbakır için veritabanından gelen cevap bu olacak
  final List<ShippingOption> options = [
    ShippingOption('BAYKAN NAKLİYE', 'TIR (25 Ton)', 2.69, 'TR16', isCheapest: false),
    ShippingOption('ÇALIŞKAN LOJİSTİK', 'TIR (Standart)', 2.27, 'TR16', isCheapest: true), // Çalışkan daha ucuz görünüyor
    ShippingOption('BAYKAN NAKLİYE', 'KIRKAYAK', 3.78, 'TR16', isCheapest: false),
  ];

  showModalBottomSheet(
    context: context,
    backgroundColor: Colors.transparent,
    builder: (context) {
      return Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Başlık ve Kapat Butonu
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text("Nakliye Seçimi", style: TextStyle(color: Colors.grey[600], fontSize: 14)),
                    Text(destination, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                  ],
                ),
                IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(context)),
              ],
            ),
            const Divider(),
            const SizedBox(height: 10),

            // LİSTE (Kartlar)
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: options.length,
                itemBuilder: (context, index) {
                  final opt = options[index];
                  return _buildShippingCard(context, opt, onSelected);
                },
              ),
            ),
          ],
        ),
      );
    },
  );
}

// Tekil Kart Tasarımı
Widget _buildShippingCard(BuildContext context, ShippingOption option, Function(ShippingOption) onTap) {
  // Çalışkan için Turuncu, Baykan için Mavi tema (Örnek)
  final Color brandColor = option.companyName.contains('ÇALIŞKAN') ? Colors.orange.shade800 : Colors.blue.shade800;

  return GestureDetector(
    onTap: () {
      onTap(option); // Seçimi ana ekrana gönder
      Navigator.pop(context); // Pencereyi kapat
    },
    child: Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border.all(
          color: option.isCheapest ? Colors.green : Colors.grey.shade300, 
          width: option.isCheapest ? 2 : 1
        ),
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 4))
        ],
      ),
      child: Row(
        children: [
          // 1. İkon ve Marka Rengi
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: brandColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(Icons.local_shipping, color: brandColor, size: 28),
          ),
          const SizedBox(width: 16),

          // 2. Firma ve Araç Bilgisi
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  option.companyName,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
                Text(
                  option.vehicleType,
                  style: TextStyle(color: Colors.grey[600], fontSize: 13),
                ),
                if (option.isCheapest) // Eğer en ucuzsa etiketi göster
                  Container(
                    margin: const EdgeInsets.top(4),
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(color: Colors.green[100], borderRadius: BorderRadius.circular(4)),
                    child: const Text(
                      "EN UYGUN FİYAT",
                      style: TextStyle(color: Colors.green, fontSize: 10, fontWeight: FontWeight.bold),
                    ),
                  )
              ],
            ),
          ),

          // 3. Fiyat Kısmı
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                "${option.pricePerKg.toStringAsFixed(2)} TL",
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.black87),
              ),
              const Text(" / Kg", style: TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
          const SizedBox(width: 8),
          const Icon(Icons.chevron_right, color: Colors.grey),
        ],
      ),
    ),
  );
}