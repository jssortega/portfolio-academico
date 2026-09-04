import 'package:finance_tfg/pantallas/pantallas.dart';
import 'package:flutter/material.dart';

class FinancePaginaPrincipal extends StatefulWidget {
  const FinancePaginaPrincipal({super.key});

  @override
  State<FinancePaginaPrincipal> createState() => _FinancePaginaPrincipalState();
}

class _FinancePaginaPrincipalState extends State<FinancePaginaPrincipal> {
  int _categoriaActiva = 1;
  static var paginas = <Widget>[
    PrevisorPantalla(),
    InicioPantalla(),
    EstadisticasPantalla()
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: paginas[_categoriaActiva],
      bottomNavigationBar: NavigationBar(
        onDestinationSelected: (int index) {
          setState(() {
            _categoriaActiva = index;
          });
        },
        backgroundColor: Color(0xFFFFFFFF),
        indicatorColor: Color(0xFF1E293B),
        selectedIndex: _categoriaActiva,
        destinations: const <Widget>[
          NavigationDestination(
            selectedIcon: Icon(Icons.calculate, color: Color(0xFFFFFFFF),),
            icon: Icon(Icons.calculate_outlined, color: Color(0xFF94A3B8)),
            label: 'Previsor',
          ),
          NavigationDestination(
            selectedIcon: Icon(Icons.home, color: Color(0xFFFFFFFF)),
            icon: Icon(Icons.home_outlined,color: Color(0xFF94A3B8)),
            label: 'Inicio',
          ),
          NavigationDestination(
            selectedIcon: Icon(Icons.analytics, color: Color(0xFFFFFFFF),),
            icon: Icon(Icons.analytics_outlined, color: Color(0xFF94A3B8),),
            label: 'Estadísticas',
          ),
        ],
      ),
    );
  }

}
