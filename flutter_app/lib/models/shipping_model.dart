class ShippingOption {
  final String city;
  final String company;
  final String factory;
  final String vehicleType;
  final double pricePerKg;

  ShippingOption({
    required this.city,
    required this.company,
    required this.factory,
    required this.vehicleType,
    required this.pricePerKg,
  });

  factory ShippingOption.fromJson(Map<String, dynamic> json) {
    return ShippingOption(
      city: json['Sehir'] ?? '',
      company: json['Firma'] ?? '',
      factory: json['Fabrika'] ?? '',
      vehicleType: json['Arac_Tipi'] ?? '',
      pricePerKg: (json['Fiyat_TL_KG'] ?? 0).toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'Sehir': city,
      'Firma': company,
      'Fabrika': factory,
      'Arac_Tipi': vehicleType,
      'Fiyat_TL_KG': pricePerKg,
    };
  }
}
