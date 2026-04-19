import 'package:flutter/material.dart';
import 'package:flutter_sesion_5/pong_pagina_principal.dart';

class PongApp extends StatelessWidget {
  const PongApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Pong Application',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blueGrey,
        ),
        useMaterial3: true,
      ),
      home: const PongPaginaPrincipal(titulo: 'Juego Pong',),
    );
  }
}
