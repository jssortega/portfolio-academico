import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:finance_tfg/modelo/modelo.dart';

class FirebaseInvitacionDao implements InviatacionDao{
  @override
  Future<void> crearInvitacion(Invitacion invitacion) async {
    try{
      final doc = FirebaseFirestore.instance.collection('Invitacion').doc();

      await doc.set({
        'id': doc.id,
        'uidOrigen': invitacion.getUidOrigen(),
        'uidDestino': invitacion.getUidDestino(),
        'cuentaId': invitacion.getCuentaId(),
        'rolAsignado': invitacion.getRolAsignado(),
        'estado': invitacion.getEstado(),
        'nombreUsuarioOrigen': invitacion.getNombreUsuarioOrigen(),
        'nombreCuenta': invitacion.getNombreCuenta()
      });

    }catch(e){
      print(e);
    }
  }

  @override
  Stream<List<Invitacion>> getInvitacionesPendientes(String uid) {
    return FirebaseFirestore.instance.collection('Invitacion').where('uidDestino', isEqualTo: uid).where('estado', isEqualTo: "Pendiente").snapshots().map((snapshot) {
      return snapshot.docs.map((doc) {
        return Invitacion.fromMap(doc.data());
      }).toList();
    });
  }

  @override
  Future<void> aceptarInvitacion(String invitacionId) async {
    try{
      final doc = FirebaseFirestore.instance.collection('Invitacion').doc(invitacionId);

      await doc.update({
        'estado': "Aceptada"
      });

      final invitacion = await doc.get();
      final data = invitacion.data() as Map<String, dynamic>;

      final String uidDestino = data['uidDestino'];
      final String cuentaId = data['cuentaId'];
      final String rolAsignado = data['rolAsignado'];

      await FirebaseFirestore.instance.collection('Usuario_Cuenta').add({
        'usuario_id': uidDestino,
        'cuenta_id': cuentaId,
        'rol': rolAsignado,
      });

    }catch(e){
      print(e);
    }
  }

  @override
  Future<void> rechazarInvitacion(String invitacionId) async {
    final doc = FirebaseFirestore.instance.collection('Invitacion').doc(invitacionId);

    await doc.update({
      'estado': "Rechazada"
    });
  }

}