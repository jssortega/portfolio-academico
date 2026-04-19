import 'package:flutter/material.dart';
import 'package:flutter_sesion_1/conversor_pagina_principal.dart';

class  ConversorApp extends StatelessWidget {
  const ConversorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Conversor',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.blue
        ),
        useMaterial3: true,
      ),
      home: const ConversorPaginaPrincipal(),
    );
  }
}
