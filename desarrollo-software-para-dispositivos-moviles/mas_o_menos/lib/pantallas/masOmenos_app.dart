import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:mas_o_menos/modelo/modelo.dart';
import 'pantallas.dart';

class MasOMenosApp extends StatelessWidget {
  const MasOMenosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Prueba',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.blueGrey,
        ),
        useMaterial3: true,
      ),
      home: MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (context) => Juego()),
          ChangeNotifierProvider(create: (context) => EstadoJuego.instancia)
        ],
        child: MasOMenosPaginaPrincipal(titulo: 'masOmenos',),
      ),
    );
  }
}
