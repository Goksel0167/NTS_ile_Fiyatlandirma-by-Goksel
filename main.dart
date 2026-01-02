import 'package:flutter/material.dart';
import 'package:nts_mobil/ui/screens/dashboard_screen.dart';

void main() {
  runApp(const NtsMobilApp());
}

class NtsMobilApp extends StatelessWidget {
  const NtsMobilApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NTS Mobil',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        // Sizin sektörün (İnşaat/Kimya) ağırlığına uygun renk paleti
        primaryColor: const Color(0xFFD32F2F), // Kırmızı (Canlılık/Dikkat)
        scaffoldBackgroundColor: const Color(0xFFF5F5F5), // Açık Gri Zemin
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFD32F2F),
          secondary: const Color(0xFF212121), // Koyu Gri (Metinler)
        ),
        useMaterial3: true,
        fontFamily: 'Roboto', // Okunaklı endüstriyel font
      ),
      home: const DashboardScreen(), // Direkt Ana Ekrana yönlendiriyoruz
    );
  }
}