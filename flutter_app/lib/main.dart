import 'package:flutter/material.dart';
import 'ui/screens/dashboard_screen.dart';

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
        primaryColor: const Color(0xFFD32F2F), // Sika Kırmızısı
        scaffoldBackgroundColor: const Color(0xFFF5F5F5),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFD32F2F),
          secondary: const Color(0xFF212121),
        ),
        useMaterial3: true,
        fontFamily: 'Roboto',
        
        // Optimized theme components
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
          backgroundColor: Color(0xFFD32F2F),
          foregroundColor: Colors.white,
        ),
        
        cardTheme: CardTheme(
          elevation: 4,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(vertical: 16),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
        
        inputDecorationTheme: InputDecorationTheme(
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 12,
          ),
        ),
      ),
      home: const DashboardScreen(),
    );
  }
}
