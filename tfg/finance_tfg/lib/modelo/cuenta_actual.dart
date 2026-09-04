import 'package:flutter/cupertino.dart';
import 'package:finance_tfg/modelo/modelo.dart';

class CuentaActual extends ChangeNotifier{
  CuentaConRol? _cuentaActual;

  CuentaConRol? getCuentaActual(){
    return _cuentaActual;
  }

  bool hayCuentaSeleccionada(){
    return _cuentaActual != null;
  }

  void seleccionarCuenta(CuentaConRol cuentaSeleccionada){
    _cuentaActual = cuentaSeleccionada;
    notifyListeners();
  }

  void actualizarSaldoActual(double nuevoSaldo) {
    if (_cuentaActual != null) {
      _cuentaActual!.cuenta.setSaldo(nuevoSaldo);
      notifyListeners();
    }
  }

  void editarCuenta(String nuevoNombre, double nuevoSaldo){
    if (_cuentaActual != null) {
      _cuentaActual!.cuenta.editarCuenta(nuevoNombre, nuevoSaldo);
      AccesoBBDD.instancia.editarCuenta(getCuentaActual()!.cuenta.getId(), nuevoNombre, nuevoSaldo);
      notifyListeners();
    }
  }

  void salirCuenta(){
    _cuentaActual = null;
    notifyListeners();
  }

  bool esConsultor() {
    return _cuentaActual?.rol == Rol.consultor;
  }

  bool esAdministrador() {
    return _cuentaActual?.rol == Rol.administrador;
  }

}