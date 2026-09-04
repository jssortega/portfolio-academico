class Invitacion{
  final String _id;
  final String _uidOrigen;
  final String _uidDestino;
  final String _cuentaId;
  final String _rolAsignado;
  final String _estado;
  final String _nombreUsuarioOrigen;
  final String _nombreCuenta;

  Invitacion({String id = "", required String uidOrigen, required String uidDestino, required String cuentaId, required String rolAsignado, required String estado, required String nombreUsuarioOrigen, required String nombreCuenta}):
    _id = id,
    _uidOrigen = uidOrigen,
    _uidDestino = uidDestino,
    _cuentaId = cuentaId,
    _rolAsignado = rolAsignado,
    _estado = estado,
    _nombreUsuarioOrigen = nombreUsuarioOrigen,
    _nombreCuenta = nombreCuenta;

  String getId() => _id;

  String getUidOrigen() => _uidOrigen;

  String getUidDestino() => _uidDestino;

  String getCuentaId() => _cuentaId;

  String getRolAsignado() => _rolAsignado;

  String getEstado() => _estado;

  String getNombreUsuarioOrigen() => _nombreUsuarioOrigen;

  String getNombreCuenta() => _nombreCuenta;

  factory Invitacion.fromMap(Map<String, dynamic> data) {
    return Invitacion(
      id: data['id'],
      uidOrigen: data['uidOrigen'],
      uidDestino: data['uidDestino'],
      cuentaId: data['cuentaId'],
      rolAsignado: data['rolAsignado'],
      estado: data['estado'],
      nombreUsuarioOrigen: data['nombreUsuarioOrigen'],
      nombreCuenta: data['nombreCuenta']
    );
  }
}