import 'package:flutter/material.dart';
import 'package:finance_tfg/utils/global.dart';
import 'modelo.dart';


enum TipoMovimiento{
  ingreso, gasto
}

enum TipoRecurrencia{
  unico, recurrente
}

enum RecurrenciaMovimiento{
  diario(EstrategiaDiaria()),
  semanal(EstrategiaSemanal()),
  mensual(EstrategiaMensual()),
  anual(EstrategiaAnual());

  final EstrategiaRecurrencia estrategia;

  const RecurrenciaMovimiento(this.estrategia);

  List<Movimiento> generarMovimientosPendientes(Movimiento movimiento, DateTime fechaActual) {
    return estrategia.generarMovimientosPendientes(movimiento, fechaActual);
  }
}

enum Categoria{
  ocio(Icons.liquor, Color(0xFFEA580C)),
  trabajo(Icons.cases,  Color(0xFF059669)),
  viaje(Icons.flight, Color(0xFF2563EB)),
  hogar(Icons.home, Colors.pink);

  final IconData icono;
  final Color colorIcono;
  const Categoria(this.icono, this.colorIcono);

  String nombre(BuildContext context) {
    final textos = AppLocalizations.of(context)!;

    switch (this) {
      case Categoria.ocio:
        return textos.ocioCategoria;
      case Categoria.trabajo:
        return textos.trabajoCategoria;
      case Categoria.viaje:
        return textos.viajeCategoria;
      case Categoria.hogar:
        return textos.hogarCategoria;
    }
  }
}

enum Rol{
  administrador(icono: Icons.admin_panel_settings),
  consultor(icono: Icons.remove_red_eye);

  const Rol({required this.icono});

  final IconData icono;

  String nombre(BuildContext context) {
    final textos = AppLocalizations.of(context)!;

    switch (this) {
      case Rol.administrador:
        return textos.administradorRol;
      case Rol.consultor:
        return textos.consultorRol;
    }
  }

  String explicacion(BuildContext context) {
    final textos = AppLocalizations.of(context)!;

    switch (this) {
      case Rol.administrador:
        return textos.administradorRolExplicacion;
      case Rol.consultor:
        return textos.consultorRolExplicacion;
    }
  }
}

enum Idioma{
  espaniol("🇪🇸", "Español"),
  ingles("🇬🇧", "English");

  final String bandera;
  final String nombre;
  const Idioma(this.bandera, this.nombre);
}

enum Divisa{
  euro("€", "Euro", "EUR"),
  dolarAmericano("\$", "American dollar", "USD");

  final String simbolo;
  final String nombre;
  final String siglas;
  const Divisa(this.simbolo, this.nombre, this.siglas);
}

enum Error{
  estadoNull(null),
  importeNoValido("El importe no es valido"),
  importeNegativo("El importe no puede ser negativo"),
  importeDosDecimales("Máximo 2 decimales");

  final String? mensaje;
  const Error(this.mensaje);
}
