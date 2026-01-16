import 'package:flutter/material.dart';
import '../../models/calculation_result.dart';

class ResultScreen extends StatelessWidget {
  final CalculationResult result;
  final String selectedCurrency;
  final Map<String, double> exchangeRates;

  const ResultScreen({
    super.key,
    required this.result,
    required this.selectedCurrency,
    required this.exchangeRates,
  });

  @override
  Widget build(BuildContext context) {
    final price = result.salesPrices[selectedCurrency] ?? 0.0;
    final rate = exchangeRates[selectedCurrency] ?? 1.0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Hesaplama Sonucu'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Ana Fiyat Kartı
            Card(
              color: result.isCheapest ? Colors.green[50] : Colors.white,
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    if (result.isCheapest)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.green,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: const Text(
                          '✓ EN UCUZ SEÇENEK',
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    const SizedBox(height: 16),
                    Text(
                      '${price.toStringAsFixed(2)} $selectedCurrency',
                      style: const TextStyle(
                        fontSize: 48,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFD32F2F),
                      ),
                    ),
                    const Text(
                      'Satış Fiyatı (kg)',
                      style: TextStyle(fontSize: 16, color: Colors.grey),
                    ),
                    const Divider(height: 32),
                    _buildPriceRow('Ton Fiyatı', 
                      '${(price * 1000).toStringAsFixed(2)} $selectedCurrency'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Detay Bilgileri
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Maliyet Detayları',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _buildDetailRow('Fabrika', result.factory),
                    _buildDetailRow('Nakliye Firması', result.company),
                    _buildDetailRow('Araç Tipi', result.vehicleType),
                    const Divider(),
                    _buildPriceRow('NTS Maliyeti', '${result.ntsCost.toStringAsFixed(2)} ₺'),
                    _buildPriceRow('Nakliye Maliyeti', '${result.shippingCost.toStringAsFixed(2)} ₺'),
                    _buildPriceRow('Toplam Maliyet', '${result.totalCost.toStringAsFixed(2)} ₺', 
                      isBold: true),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Tüm Dövizler
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Diğer Döviz Kurları',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    ...result.salesPrices.entries.map((entry) {
                      return _buildPriceRow(
                        entry.key,
                        '${entry.value.toStringAsFixed(2)} ${entry.key}/kg',
                      );
                    }),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Geri Dön Butonu
            SizedBox(
              height: 56,
              child: ElevatedButton.icon(
                onPressed: () => Navigator.pop(context),
                icon: const Icon(Icons.arrow_back),
                label: const Text(
                  'YENİ HESAPLAMA',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFD32F2F),
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPriceRow(String label, String value, {bool isBold = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 16,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 16,
              fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
              color: isBold ? const Color(0xFFD32F2F) : Colors.black87,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}
