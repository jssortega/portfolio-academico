import 'package:flutter/cupertino.dart';

class EstadoJuego extends ChangeNotifier{
  bool _jugando = false;

  static final EstadoJuego _instancia = EstadoJuego._();

  EstadoJuego._();

  static EstadoJuego get instancia => _instancia;
  static bool get jugando => _instancia._jugando;

  set estado(bool cambioEstado){
    _jugando = cambioEstado;
    notifyListeners();
  }

}
