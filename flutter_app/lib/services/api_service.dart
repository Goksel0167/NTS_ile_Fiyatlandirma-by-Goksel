import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/product_model.dart';
import '../models/shipping_model.dart';
import '../models/calculation_result.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8501'; // Streamlit backend
  
  // Ürünleri getir
  Future<List<Product>> fetchProducts() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/products'));
      if (response.statusCode == 200) {
        List<dynamic> data = json.decode(response.body);
        return data.map((json) => Product.fromJson(json)).toList();
      }
      throw Exception('Ürünler yüklenemedi');
    } catch (e) {
      throw Exception('Bağlantı hatası: $e');
    }
  }
  
  // Şehirleri getir
  Future<List<String>> fetchCities() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/cities'));
      if (response.statusCode == 200) {
        List<dynamic> data = json.decode(response.body);
        return data.cast<String>();
      }
      throw Exception('Şehirler yüklenemedi');
    } catch (e) {
      throw Exception('Bağlantı hatası: $e');
    }
  }
  
  // Nakliye seçeneklerini getir
  Future<List<ShippingOption>> fetchShippingOptions(String city) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/shipping?city=$city')
      );
      if (response.statusCode == 200) {
        List<dynamic> data = json.decode(response.body);
        return data.map((json) => ShippingOption.fromJson(json)).toList();
      }
      throw Exception('Nakliye seçenekleri yüklenemedi');
    } catch (e) {
      throw Exception('Bağlantı hatası: $e');
    }
  }
  
  // Fiyat hesapla
  Future<CalculationResult> calculatePrice({
    required String product,
    required String city,
    required double profitMargin,
    String? factory,
    String? shippingCompany,
    String? vehicleType,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/calculate'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'product': product,
          'city': city,
          'profit_margin': profitMargin,
          'factory': factory,
          'shipping_company': shippingCompany,
          'vehicle_type': vehicleType,
        }),
      );
      
      if (response.statusCode == 200) {
        return CalculationResult.fromJson(json.decode(response.body));
      }
      throw Exception('Hesaplama başarısız');
    } catch (e) {
      throw Exception('Hesaplama hatası: $e');
    }
  }
  
  // Döviz kurlarını getir
  Future<Map<String, double>> fetchExchangeRates() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/rates'));
      if (response.statusCode == 200) {
        Map<String, dynamic> data = json.decode(response.body);
        return data.map((key, value) => MapEntry(key, value.toDouble()));
      }
      throw Exception('Kurlar yüklenemedi');
    } catch (e) {
      throw Exception('Bağlantı hatası: $e');
    }
  }
}
