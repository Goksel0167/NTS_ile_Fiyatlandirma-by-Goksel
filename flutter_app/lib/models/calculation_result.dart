class CalculationResult {
  final String factory;
  final String company;
  final String vehicleType;
  final double ntsCost;
  final double shippingCost;
  final double totalCost;
  final Map<String, double> salesPrices; // TL, USD, EUR, CHF
  final bool isCheapest;

  CalculationResult({
    required this.factory,
    required this.company,
    required this.vehicleType,
    required this.ntsCost,
    required this.shippingCost,
    required this.totalCost,
    required this.salesPrices,
    this.isCheapest = false,
  });

  factory CalculationResult.fromJson(Map<String, dynamic> json) {
    return CalculationResult(
      factory: json['Fabrika'] ?? '',
      company: json['Firma'] ?? '',
      vehicleType: json['Arac'] ?? '',
      ntsCost: (json['NTS_TL'] ?? 0).toDouble(),
      shippingCost: (json['Nakliye_TL'] ?? 0).toDouble(),
      totalCost: (json['Toplam_Maliyet_TL'] ?? 0).toDouble(),
      salesPrices: {
        'TL': (json['Satis_TL'] ?? 0).toDouble(),
        'USD': (json['Satis_USD_KG'] ?? 0).toDouble(),
        'EUR': (json['Satis_EUR_KG'] ?? 0).toDouble(),
        'CHF': (json['Satis_CHF_KG'] ?? 0).toDouble(),
      },
      isCheapest: json['is_cheapest'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'Fabrika': factory,
      'Firma': company,
      'Arac': vehicleType,
      'NTS_TL': ntsCost,
      'Nakliye_TL': shippingCost,
      'Toplam_Maliyet_TL': totalCost,
      'Satis_TL': salesPrices['TL'],
      'Satis_USD_KG': salesPrices['USD'],
      'Satis_EUR_KG': salesPrices['EUR'],
      'Satis_CHF_KG': salesPrices['CHF'],
      'is_cheapest': isCheapest,
    };
  }
}
