class Cuenta{
  final String _id;
  String _nombre;
  double _saldo;

  Cuenta({String id = "", required String nombre, required double saldo}): _id = id, _nombre = nombre, _saldo = saldo;

  String getId() => _id;

  String getNombre() => _nombre;

  double getSaldo() => _saldo;

  void setSaldo(double nuevoSaldo) {
    _saldo = nuevoSaldo;
  }

  void editarCuenta(String nuevoNombre, double nuevoSaldo){
    _nombre = nuevoNombre;
    _saldo = nuevoSaldo;
  }

  factory Cuenta.fromMap(Map<String, dynamic> data, String cuentaID) {
    return Cuenta(
      id: cuentaID,
      nombre: data['nombre'] ?? '',
      saldo: data['saldo'] ?? 0,
    );
  }

}