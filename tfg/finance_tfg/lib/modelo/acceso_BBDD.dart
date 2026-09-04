import 'dart:io';

import 'package:finance_tfg/modelo/firebase_cuenta_dao.dart';
import 'package:finance_tfg/modelo/firebase_movimiento_dao.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:flutter/cupertino.dart';

/// Singleton que se utiliza para las llamadas a los métodos que gestionan la BBDD
class AccesoBBDD extends ChangeNotifier{

  /// Declaración de los tres objetos que tienen su correspondiente tabla en la BBDD
  late UsuarioDAO _usuarioDAO;
  late CuentaDao _cuentaDao;
  late MovimientoDAO _movimientoDAO;
  late InviatacionDao _inviatacionDao;

  /// Objeto de la propia clase para iniciarlo y acceder a la misma
  static final AccesoBBDD instancia = AccesoBBDD._init();

  /// Constructor que inicializa los objetos UsuarioDAO, CuentaDAO y MovimientoDAO
  AccesoBBDD._init(){
    _usuarioDAO = FirebaseUsuarioDAO();
    _cuentaDao = FirebaseCuentaDao();
    _movimientoDAO = FirebaseMovimientoDAO();
    _inviatacionDao = FirebaseInvitacionDao();
  }

  /// Conjunto de métodos de Usuario
  Future<void> inicioSesion(String email, String contrasena) => _usuarioDAO.inicioSesion(email, contrasena);

  Future<void> registrarUsuario(Usuario usuario, String contrasena) => _usuarioDAO.registrarUsuario(usuario,contrasena);

  Future<void> cerrarSesion() => _usuarioDAO.cerrarSesion();

  String? _getUidUsuarioActual() => _usuarioDAO.getUidUsuarioActual();

  Stream<Usuario?> getUsuarioActual(){
    final uid = _getUidUsuarioActual();
    return _usuarioDAO.streamUsuario(uid!);
  }

  Stream<List<UsuarioConRol>> getUsuariosCuentas(String idCuenta) => _usuarioDAO.getUsuariosCuentaActual(idCuenta);

  Future<void> actualizarUsuario(String nuevoNombre, String nuevoNombreUsuario, String nuevoEmail, File? imagenPerfil, String? contrasenaActual) => _usuarioDAO.modificarUsuario(nuevoNombre, nuevoNombreUsuario, nuevoEmail, imagenPerfil, contrasenaActual);

  Future<Usuario?> buscarUsuarioPorUid(String uid) => _usuarioDAO.buscarUsuarioPorUid(uid);

  Future<List<Usuario>> buscarUsuariosPorNombre(String nombreUsuario) => _usuarioDAO.buscarUsuariosPorNombre(nombreUsuario);

  Future<void> eliminarUsuario(String uid, String contrasena) => _usuarioDAO.eliminarUsuario(uid, contrasena);

  /// Conjunto de métodos de Cuenta
  Future<void> anadirCuenta(Cuenta cuenta) => _cuentaDao.aniadirCuenta(cuenta, _getUidUsuarioActual() ?? "");

  Future<void> editarCuenta(String idCuenta, String nuevoNombre, double nuevoSaldo) => _cuentaDao.editarCuenta(idCuenta, nuevoNombre, nuevoSaldo);

  Future<void> eliminarCuenta(String idCuenta) => _cuentaDao.eliminarCuenta(idCuenta);
  
  Stream<List<CuentaConRol>> getCuentasUsuario() => _cuentaDao.getCuentasUsuarioActual(_getUidUsuarioActual() ?? "");

  Future<void> acutalizarSaldo(String cuentaId, double nuevoSaldo) => _cuentaDao.actualizarSaldo(cuentaId, nuevoSaldo);

  Future<void> actualizarRol(String idCuenta, String uid, String nuevoRol) => _cuentaDao.actualizarRol(idCuenta, uid, nuevoRol);
  
  /// Conjunto de métodos de Movimiento
  Future<String?> aniadirMovimiento(Movimiento movimiento, String cuentaId) => _movimientoDAO.aniadirMovimiento(movimiento, cuentaId);

  Stream<List<Movimiento>> getMovimientos(String cuentaId) => _movimientoDAO.getMovimientos(cuentaId);

  Future<File> getMovimientosRecurrentes(String cuentaId, File? movimientos) => _movimientoDAO.getMovimientosRecurrentes(cuentaId, movimientos);

  /// Conjunto de métodos de Invitacion
  Future<void> crearInvitacion(Invitacion invitacion) => _inviatacionDao.crearInvitacion(invitacion);

  Stream<List<Invitacion>> getInvitacionesPendientes(String uid) => _inviatacionDao.getInvitacionesPendientes(uid);

  Future<void> aceptarInvitacion(String invitacionId) => _inviatacionDao.aceptarInvitacion(invitacionId);

  Future<void> rechazarInvitacion(String invitacionId) => _inviatacionDao.rechazarInvitacion(invitacionId);

}