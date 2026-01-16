import 'package:flutter/material.dart';
import '../../services/api_service.dart';
import '../../models/product_model.dart';
import '../../models/shipping_model.dart';
import '../../models/calculation_result.dart';
import 'result_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final ApiService _apiService = ApiService();
  
  // Form state
  String? selectedProduct;
  String selectedCurrency = 'EUR';
  double profitMargin = 15.0;
  String? selectedCity;
  List<Product> products = [];
  List<String> cities = [];
  List<ShippingOption> shippingOptions = [];
  ShippingOption? selectedShipping;
  
  bool isLoading = false;
  String? errorMessage;
  Map<String, double> exchangeRates = {};

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => isLoading = true);
    
    try {
      // Paralel yükleme - optimizasyon
      final results = await Future.wait([
        _apiService.fetchProducts(),
        _apiService.fetchCities(),
        _apiService.fetchExchangeRates(),
      ]);
      
      setState(() {
        products = results[0] as List<Product>;
        cities = results[1] as List<String>;
        exchangeRates = results[2] as Map<String, double>;
        isLoading = false;
        errorMessage = null;
      });
    } catch (e) {
      setState(() {
        isLoading = false;
        errorMessage = 'Veri yüklenemedi: $e';
      });
    }
  }

  Future<void> _loadShippingOptions(String city) async {
    setState(() => isLoading = true);
    
    try {
      final options = await _apiService.fetchShippingOptions(city);
      setState(() {
        shippingOptions = options;
        isLoading = false;
        errorMessage = null;
      });
      
      // Nakliye seçim dialogunu aç
      if (options.isNotEmpty) {
        _showShippingDialog();
      }
    } catch (e) {
      setState(() {
        isLoading = false;
        errorMessage = 'Nakliye seçenekleri yüklenemedi: $e';
      });
    }
  }

  void _showShippingDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        minChildSize: 0.4,
        expand: false,
        builder: (context, scrollController) {
          return Column(
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: Color(0xFFD32F2F),
                  borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.local_shipping, color: Colors.white),
                    SizedBox(width: 12),
                    Text(
                      'Nakliye Firması Seçin',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: ListView.builder(
                  controller: scrollController,
                  itemCount: shippingOptions.length,
                  padding: const EdgeInsets.all(16),
                  itemBuilder: (context, index) {
                    final option = shippingOptions[index];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: const Color(0xFFD32F2F),
                          child: Text(
                            option.factory.replaceAll('TR', ''),
                            style: const TextStyle(color: Colors.white),
                          ),
                        ),
                        title: Text(
                          '${option.company} - ${option.vehicleType}',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Text(
                          'Fabrika: ${option.factory}\n${option.pricePerKg.toStringAsFixed(2)} ₺/kg',
                        ),
                        isThreeLine: true,
                        trailing: const Icon(Icons.arrow_forward_ios, size: 16),
                        onTap: () {
                          setState(() => selectedShipping = option);
                          Navigator.pop(context);
                        },
                      ),
                    );
                  },
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _calculatePrice() async {
    if (selectedProduct == null || selectedCity == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lütfen ürün ve şehir seçin')),
      );
      return;
    }

    setState(() => isLoading = true);

    try {
      final result = await _apiService.calculatePrice(
        product: selectedProduct!,
        city: selectedCity!,
        profitMargin: profitMargin,
        factory: selectedShipping?.factory,
        shippingCompany: selectedShipping?.company,
        vehicleType: selectedShipping?.vehicleType,
      );

      if (mounted) {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ResultScreen(
              result: result,
              selectedCurrency: selectedCurrency,
              exchangeRates: exchangeRates,
            ),
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hesaplama hatası: $e')),
      );
    } finally {
      if (mounted) {
        setState(() => isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('NTS Mobil'),
        actions: [
          IconButton(
            onPressed: _loadInitialData,
            icon: const Icon(Icons.refresh),
            tooltip: 'Yenile',
          ),
        ],
      ),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : errorMessage != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 64, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(errorMessage!),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadInitialData,
                        child: const Text('Tekrar Dene'),
                      ),
                    ],
                  ),
                )
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _buildProductSection(),
                      const SizedBox(height: 20),
                      _buildShippingSection(),
                      const SizedBox(height: 20),
                      _buildProfitMarginSection(),
                      const SizedBox(height: 30),
                      _buildCalculateButton(),
                    ],
                  ),
                ),
    );
  }

  Widget _buildProductSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Ürün Maliyet Girişi',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(
                labelText: 'Ürün Seçiniz',
                prefixIcon: Icon(Icons.layers),
              ),
              value: selectedProduct,
              items: products.map((product) {
                return DropdownMenuItem(
                  value: product.name,
                  child: Text(product.name),
                );
              }).toList(),
              onChanged: (val) => setState(() => selectedProduct = val),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(child: _buildCurrencySelector()),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildShippingSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Lojistik Planlama',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(
                labelText: 'Varış Noktası',
                prefixIcon: Icon(Icons.location_on),
              ),
              value: selectedCity,
              items: cities.map((city) {
                return DropdownMenuItem(value: city, child: Text(city));
              }).toList(),
              onChanged: (val) {
                setState(() {
                  selectedCity = val;
                  selectedShipping = null;
                });
              },
            ),
            if (selectedCity != null) ...[
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: () => _loadShippingOptions(selectedCity!),
                  icon: const Icon(Icons.search),
                  label: Text(
                    selectedShipping != null
                        ? '${selectedShipping!.company} - ${selectedShipping!.vehicleType}'
                        : 'Nakliye Seçin',
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueGrey[800],
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildProfitMarginSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Kâr Marjı: %${profitMargin.toInt()}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            Slider(
              value: profitMargin,
              min: 0,
              max: 100,
              divisions: 100,
              activeColor: const Color(0xFFD32F2F),
              onChanged: (val) => setState(() => profitMargin = val),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCurrencySelector() {
    final currencies = ['TL', 'USD', 'EUR', 'CHF'];
    return SegmentedButton<String>(
      segments: currencies.map((currency) {
        return ButtonSegment(
          value: currency,
          label: Text(currency),
        );
      }).toList(),
      selected: {selectedCurrency},
      onSelectionChanged: (Set<String> selected) {
        setState(() => selectedCurrency = selected.first);
      },
    );
  }

  Widget _buildCalculateButton() {
    return SizedBox(
      height: 56,
      child: ElevatedButton(
        onPressed: _calculatePrice,
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFFD32F2F),
          foregroundColor: Colors.white,
        ),
        child: const Text(
          'FİYAT HESAPLA',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
      ),
    );
  }
}
