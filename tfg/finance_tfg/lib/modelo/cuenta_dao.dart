import "package:finance_tfg/modelo/modelo.dart";

abstract class CuentaDao{
  Future<void> aniadirCuenta(Cuenta cuenta, String uid);

  Future<void> editarCuenta(String idCuenta, String nuevoNombre, double nuevoSaldo);

  Future<void> eliminarCuenta(String idCuenta);

  Stream<List<CuentaConRol>> getCuentasUsuarioActual(String uid);

  Future<void> actualizarSaldo(String idCuenta, double nuevoSaldo);

  Future<void> actualizarRol(String idCuenta, String uid, String nuevoRol);
}