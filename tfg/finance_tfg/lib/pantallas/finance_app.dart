import 'package:finance_tfg/modelo/modelo.dart';
import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:finance_tfg/l10n/app_localizations.dart';
import 'package:provider/provider.dart';

class FinanceApp extends StatelessWidget {
  const FinanceApp({super.key});

  @override
  Widget build(BuildContext context) {
    final preferenciasIdioma = Provider.of<PreferenciasIdioma>(context, listen: true);

    return MovimientosProvider(
      child: ScreenUtilInit(
        designSize: const Size(411, 866),
        minTextAdapt: true,
        splitScreenMode: true,
        builder: (context, child) {
          return MaterialApp(
            title: 'Finance',
            debugShowCheckedModeBanner: false,
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
              useMaterial3: true,
            ),

            locale: preferenciasIdioma.getIdiomaActual(),

            localizationsDelegates: const [
              AppLocalizations.delegate,
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],

            supportedLocales: const [
              Locale('en'),
              Locale('es'),
            ],

            home: const FinanceAtentificacionApp(),
          );
        },
      ),
    );
  }
}