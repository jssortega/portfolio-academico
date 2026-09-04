import 'package:flutter/cupertino.dart';

class PreferenciasIdioma extends ChangeNotifier{
  Locale? _idiomaActual;

  Locale? getIdiomaActual() => _idiomaActual;

  void cambiarIdioma(Locale nuevoIdioma){
    _idiomaActual = nuevoIdioma;
    notifyListeners();
  }
}