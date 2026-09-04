import 'package:finance_tfg/modelo/modelo.dart';

class Movimiento{
  String _id;
  final TipoMovimiento _tipoMovimiento;
  final TipoRecurrencia _tipoRecurrencia;
  final double _importe;
  DateTime _fecha;
  final DateTime? _fechaFin;
  final RecurrenciaMovimiento? _recurrencia;
  final Categoria _categoria;
  final String _uid;


  Movimiento({String id = "", required TipoMovimiento tipoMovimiento, required TipoRecurrencia tipoRecurrencia, required double importe, required DateTime fecha, DateTime? fechaFin, RecurrenciaMovimiento? recurrencia, required Categoria categoria, required String uid}):
    _id = id,
    _tipoMovimiento = tipoMovimiento,
    _tipoRecurrencia = tipoRecurrencia,
    _importe = importe,
    _fecha = fecha,
    _fechaFin = fechaFin,
    _recurrencia = recurrencia,
    _categoria = categoria,
    _uid = uid;

  String getId() => _id;

  void setId(String id) => _id=id;

  TipoMovimiento getTipoMovimiento() => _tipoMovimiento;

  TipoRecurrencia getTipoRecurrencia() => _tipoRecurrencia;

  double getImporte() => _importe;

  DateTime getFecha() => _fecha;

  void setFecha(DateTime fecha) => _fecha = fecha;

  DateTime? getFechaFin() => _fechaFin;

  RecurrenciaMovimiento? getRecurrencia() => _recurrencia;

  Categoria getCategoria() => _categoria;

  String getUidUsuario() => _uid;

  Movimiento copiaConFecha(DateTime nuevaFecha) {
    return Movimiento(
      id: _id,
      tipoMovimiento: _tipoMovimiento,
      tipoRecurrencia: _tipoRecurrencia,
      importe: _importe,
      fecha: nuevaFecha,
      fechaFin: _fechaFin,
      recurrencia: _recurrencia,
      categoria: _categoria,
      uid: _uid,
    );
  }

  Map<String, dynamic> toJson(){
    return {
      'id': _id,
      'tipo_movimiento': _tipoMovimiento.name,
      'tipo_recurrencia': _tipoRecurrencia.name,
      'importe': _importe,
      'fecha': _fecha.toIso8601String(),
      'fecha_fin': _fechaFin?.toIso8601String(),
      'recurrencia': _recurrencia?.name,
      'categoria': _categoria.name,
      'uid': _uid,
    };
  }

  factory Movimiento.fromJson(Map<String, dynamic> data){
    return Movimiento(
        id: data['id'] ?? '',
        tipoMovimiento: TipoMovimiento.values.firstWhere((e) => e.name == data['tipo_movimiento'],),
        tipoRecurrencia: TipoRecurrencia.values.firstWhere((e) => e.name == data['tipo_recurrencia'],),
        importe: (data['importe'] ?? 0).toDouble(),
        fecha: DateTime.parse(data['fecha']),
        fechaFin: data['fecha_fin'] != null ? DateTime.parse(data['fecha_fin']) : null,
        recurrencia: data['recurrencia'] != null ? RecurrenciaMovimiento.values.firstWhere((e) => e.name == data['recurrencia'],) : null,
        categoria: Categoria.values.firstWhere((e) => e.name == data['categoria'],),
        uid: data['uid'],
    );
  }

  factory Movimiento.fromMap(Map<String, dynamic> data) {
    return Movimiento(
      id: data['id'] ?? '',
      tipoMovimiento: TipoMovimiento.values.firstWhere((e) => e.name == data['tipo_movimiento'],),
      tipoRecurrencia: TipoRecurrencia.values.firstWhere((e) => e.name == data['tipo_recurrencia'],),
      importe: (data['importe'] ?? 0).toDouble(),
      fecha: (data['fecha']).toDate(),
      fechaFin: data['fecha_fin'] != null ? (data['fecha_fin']).toDate() : null,
      recurrencia: data['recurrencia'] != null ? RecurrenciaMovimiento.values.firstWhere((e) => e.name == data['recurrencia'],) : null,
      categoria: Categoria.values.firstWhere((e) => e.name == data['categoria'],),
      uid: data['uid'] ?? '',
    );
  }

  @override
  String toString() {
    return "$_fecha / $_importe";
  }

}