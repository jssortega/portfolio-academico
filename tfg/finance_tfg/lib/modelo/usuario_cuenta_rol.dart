import 'package:finance_tfg/modelo/modelo.dart';

class CuentaConRol {
  final Cuenta cuenta;
  final Rol rol;

  CuentaConRol({
    required this.cuenta,
    required this.rol,
  });
}

class UsuarioConRol {
  final Usuario usuario;
  final String rol;

  UsuarioConRol({
    required this.usuario,
    required this.rol,
  });
}