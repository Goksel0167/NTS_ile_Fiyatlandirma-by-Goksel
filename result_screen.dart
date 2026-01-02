import 'package:flutter/material.dart';

class ResultScreen extends StatelessWidget {
  // Bu veriler önceki sayfadan (Dashboard) geliyor
  final String productName;
  final String destination;
  final double baseCostEur; // Sizin girdiğiniz 2.50
  final double shippingCostTl; // Nakliye 2.69
  final double marginPercent; // %15

  const ResultScreen({
    super.key,
    required this.productName,
    required this.destination,
    required this.baseCostEur,
    required this.shippingCostTl,
    required this.marginPercent,
  });

  @override
  Widget build(BuildContext context) {
    // SİMÜLASYON: Arka planda hesaplama yapılıyor
    // Gerçekte burası Service katmanından gelecek
    final double eurRate = 38.20;
    final double usdRate = 36.50;
    final double chfRate = 41.10;

    // Hesaplama Mantığı (Optimize edilmiş)
    // 1. Her şeyi TL'ye çevir (Base)
    double rawCostTl = baseCostEur * eurRate;
    double totalCostTl = rawCostTl + shippingCostTl;
    double finalPriceTl = totalCostTl * (1 + marginPercent / 100);

    // 2. Diğer kurlara böl
    double finalPriceUsd = finalPriceTl / usdRate;
    double finalPriceEur = finalPriceTl / eurRate;
    double finalPriceChf = finalPriceTl / chfRate;

    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      appBar: AppBar(
        title: const Text("Fiyat Analizi", style: TextStyle(color: Colors.white)),
        backgroundColor: const Color(0xFFD32F2F),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // --- ÖZET BİLGİ KARTI ---
            _buildSummaryCard(),

            const SizedBox(height: 20),

            // --- FİYAT TABLOSU (ANA KISIM) ---
            const Text(
              "SATIŞ FİYAT LİSTESİ",
              style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 1.2, color: Colors.grey),
            ),
            const SizedBox(height: 10),
            
            _buildPriceRow("TÜRK LİRASI", "₺", finalPriceTl, Colors.red.shade50, Colors.red.shade900),
            _buildPriceRow("ABD DOLARI", "\$", finalPriceUsd, Colors.white, Colors.black87),
            _buildPriceRow("EURO", "€", finalPriceEur, Colors.blue.shade50, Colors.blue.shade900),
            _buildPriceRow("İSVİÇRE FRANGI", "₣", finalPriceChf, Colors.white, Colors.black87),

            const SizedBox(height: 30),

            // --- AKSİYON BUTONLARI ---
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.share),
                    label: const Text("WhatsApp ile Paylaş"),
                    style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 16)),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () {},
                    icon: const Icon(Icons.picture_as_pdf),
                    label: const Text("PDF Teklif Oluştur"),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF2E7D32), // WhatsApp Yeşili / PDF Rengi
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                  ),
                ),
              ],
            )
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 10)],
      ),
      child: Column(
        children: [
          Text(productName, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold), textAlign: TextAlign.center),
          const Divider(),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildInfoItem("Rota", destination),
              _buildInfoItem("Hammadde", "$baseCostEur €"),
              _buildInfoItem("Nakliye", "$shippingCostTl TL"),
              _buildInfoItem("Marj", "%${marginPercent.toInt()}"),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoItem(String label, String value) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
        Text(value, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
      ],
    );
  }

  Widget _buildPriceRow(String title, String symbol, double price, Color bgColor, Color textColor) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.grey.shade300),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Sol taraf: Para Birimi Adı
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(color: Colors.white, shape: BoxShape.circle),
                child: Text(symbol, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
              ),
              const SizedBox(width: 12),
              Text(title, style: TextStyle(fontWeight: FontWeight.bold, color: textColor)),
            ],
          ),
          
          // Sağ Taraf: KG ve TON Fiyatları
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                "${price.toStringAsFixed(2)} $symbol / Kg", 
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: textColor),
              ),
              Text(
                "${(price * 1000).toStringAsFixed(0)} $symbol / Ton",
                style: TextStyle(fontSize: 12, color: textColor.withOpacity(0.7)),
              ),
            ],
          )
        ],
      ),
    );
  }
}