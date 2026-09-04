import 'package:finance_tfg/modelo/modelo.dart';
import 'package:flutter/material.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:firebase_core/firebase_core.dart' hide FirebaseApp;
import 'package:provider/provider.dart';
import 'firebase_options.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  await dotenv.load();
  runApp(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => PreferenciasVisuales()),
          ChangeNotifierProvider(create: (_) => PreferenciasIdioma()),
          ChangeNotifierProvider(create: (_) {
            final preferenciasDivisa = PreferenciasDivisa();
            preferenciasDivisa.cargarTasas();
            return preferenciasDivisa;}
          ),
          ChangeNotifierProvider(create: (_) => CuentaActual()),
        ],
        child: const FinanceApp()
    )
  );
}