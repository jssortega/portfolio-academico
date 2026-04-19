import 'package:flutter/material.dart';
import 'package:flutter_sesion_2_4/pantallas/pantallas.dart';
import 'package:provider/provider.dart';
import '../modelo/modelo.dart';

class MonsterChefApp extends StatelessWidget {
  const MonsterChefApp({super.key});

  @override
  Widget build(BuildContext context) {
    final listaCompra = ListaCompra();
    listaCompra.init();
    return MaterialApp(
      title: 'Mosnter Chef Application',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
            seedColor: Colors.white
        ),
        brightness: Brightness.light,
        useMaterial3: true
      ),
      darkTheme: ThemeData.dark(),
      themeMode: ThemeMode.system,
      // 5
      home: MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (context) => listaCompra,),
        ],
        child: MonsterChefPaginaPrincipal(titulo: 'Monster Chef',),
      ),
    );
  }
}
