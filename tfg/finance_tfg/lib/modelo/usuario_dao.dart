import 'dart:io';

import 'package:finance_tfg/modelo/modelo.dart';

abstract class UsuarioDAO{
  Future<void>  registrarUsuario(Usuario user, String contrasena);

  Future<void> inicioSesion(String email, String contrasena);

  Future<void> cerrarSesion();

  String? getUidUsuarioActual();

  Stream<Usuario?> streamUsuario(String uid);

  Stream<List<UsuarioConRol>> getUsuariosCuentaActual(String idCuenta);

  Future<void> modificarUsuario(String nombre, String nombreUsuario, String email, File? imagenPerfil, String? contrasenaActual);

  Future<Usuario?> buscarUsuarioPorUid(String uid);

  Future<List<Usuario>> buscarUsuariosPorNombre(String nombreUsuario);

  Future<void> eliminarUsuario(String uid, String contrasena);
}