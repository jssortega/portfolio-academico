import 'package:flutter/cupertino.dart';

class PreferenciasVisuales extends ChangeNotifier{
  bool _ocultarImportes = false;

  bool getOcultarImportes() => _ocultarImportes;

  void ocultarImportes(){
    _ocultarImportes = !_ocultarImportes;
    notifyListeners();
  }
}