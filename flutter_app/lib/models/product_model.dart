class Product {
  final String name;
  final String factory;
  final double cost;
  final DateTime recordDate;

  Product({
    required this.name,
    required this.factory,
    required this.cost,
    required this.recordDate,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      name: json['Urun_Adi'] ?? '',
      factory: json['Fabrika'] ?? '',
      cost: (json['NTS_Maliyet_TL'] ?? 0).toDouble(),
      recordDate: DateTime.parse(json['Kayit_Tarihi'] ?? DateTime.now().toIso8601String()),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'Urun_Adi': name,
      'Fabrika': factory,
      'NTS_Maliyet_TL': cost,
      'Kayit_Tarihi': recordDate.toIso8601String(),
    };
  }
}
