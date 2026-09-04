import 'package:finance_tfg/modelo/modelo.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'dart:math';

class FirebaseCuentaDao implements CuentaDao {
  @override
  Future<void> aniadirCuenta(Cuenta cuenta, String uid) async {
    try{
      int idRandom = 100000 + Random().nextInt(900000);
      String idCuenta = idRandom.toString();

      FirebaseFirestore.instance.collection('Cuenta').doc(idCuenta).set({
        'id': idCuenta,
        'nombre': cuenta.getNombre(),
        'saldo': cuenta.getSaldo()
      });
      
      FirebaseFirestore.instance.collection("Usuario_Cuenta").add({
        'cuenta_id': idCuenta,
        'usuario_id': uid,
        'rol': Rol.administrador.name
      });
    }catch(e){
      print("Error al añadir la cuenta: $e");
    }
  }

  @override
  Future<void> editarCuenta(String idCuenta, String nuevoNombre, double nuevoSaldo) async {
    DocumentReference cuentaRef = FirebaseFirestore.instance.collection('Cuenta').doc(idCuenta);

    await cuentaRef.update({
      'nombre': nuevoNombre,
      'saldo': nuevoSaldo,
    });
  }

  @override
  Future<void> eliminarCuenta(String idCuenta) async {
    try {
      await FirebaseFirestore.instance.collection("Cuenta").doc(idCuenta).delete();

      final relaciones = await FirebaseFirestore.instance.collection("Usuario_Cuenta").where("cuenta_id", isEqualTo: idCuenta).get();

      for(var doc in relaciones.docs){
        await doc.reference.delete();
      }
    } catch(e){
        print(e);
    }
  }

  @override
  Stream<List<CuentaConRol>> getCuentasUsuarioActual(String uid){
    return FirebaseFirestore.instance.collection("Usuario_Cuenta").where("usuario_id", isEqualTo: uid).snapshots().asyncMap((snapshotRelacion) async {

      final List<String> idCuentas = [];
      final Map<String, String> roles = {};

      for (var doc in snapshotRelacion.docs){
        final data = doc.data();
        final String cuentaId = data["cuenta_id"];
        final String rol = data["rol"];

        idCuentas.add(cuentaId);
        roles[cuentaId] = rol;
      }

      if (idCuentas.isEmpty) {
        return <CuentaConRol>[];
      }

      final snapshotCuentas = await FirebaseFirestore.instance.collection("Cuenta").where("id", whereIn: idCuentas).get();

      return snapshotCuentas.docs.map((doc) {
        final cuenta = Cuenta.fromMap(doc.data(), doc.id);
        final String rol = roles[doc.id]!;
        return CuentaConRol(cuenta: cuenta, rol: Rol.values.byName(rol));
      }).toList();
    });
  }

  @override
  Future<void> actualizarSaldo(String idCuenta, double nuevoSaldo) async {
    FirebaseFirestore.instance.collection("Cuenta").doc(idCuenta).update({
      'saldo': nuevoSaldo,
    });
  }
  
  @override
  Future<void> actualizarRol(String idCuenta, String uid, String nuevoRol) async {
    final doc = await FirebaseFirestore.instance.collection("Usuario_Cuenta").where("usuario_id", isEqualTo: uid).where("cuenta_id", isEqualTo: idCuenta).get();

    if(doc.docs.isNotEmpty){
      await doc.docs.first.reference.update({
        "rol": nuevoRol
      });
    }

  }
}