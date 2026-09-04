import 'dart:io';

import 'package:finance_tfg/modelo/modelo.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:path_provider/path_provider.dart';

class FirebaseMovimientoDAO implements MovimientoDAO{
  @override
  Future<String?> aniadirMovimiento(Movimiento movimiento, String cuentaId) async{
    try{
      final doc = FirebaseFirestore.instance.collection('Cuenta').doc(cuentaId).collection('Movimiento').doc();

      await doc.set({
        'id': doc.id,
        'tipo_movimiento': movimiento.getTipoMovimiento().name,
        'tipo_recurrencia': movimiento.getTipoRecurrencia().name,
        'importe': movimiento.getImporte(),
        'fecha': movimiento.getFecha(),
        'fecha_fin': movimiento.getFechaFin(),
        'recurrencia': movimiento.getRecurrencia()?.name,
        'categoria': movimiento.getCategoria().name,
        'uid': movimiento.getUidUsuario(),
      });

      return doc.id;
      
    }catch(e){
      print(e);
      return null;
    }
  }

  @override
  Stream<List<Movimiento>> getMovimientos(String cuentaId) {
    return FirebaseFirestore.instance.collection('Cuenta').doc(cuentaId).collection('Movimiento').orderBy('fecha', descending: true).snapshots().map((snapshot) {
      return snapshot.docs.map((doc) {
        return Movimiento.fromMap(doc.data());
      }).toList();
    });
  }

  @override
  Future<File> getMovimientosRecurrentes(String cuentaId, File? movimientos) async {
    final storageRef = FirebaseStorage.instance.ref().child('movimientosRecurrentes').child(cuentaId).child('movimientos_recurrentes.json');

    final directorioTemporal = await getTemporaryDirectory();
    final archivoMovimientos = File('${directorioTemporal.path}/movimientos_recurrentes_$cuentaId.json');

    if(movimientos != null){
      await storageRef.putFile(movimientos);
      return movimientos;
    }

    try {
      await storageRef.writeToFile(archivoMovimientos);
    } catch (e) {
      await archivoMovimientos.writeAsString('[]');
    }

    return archivoMovimientos;
  }

}