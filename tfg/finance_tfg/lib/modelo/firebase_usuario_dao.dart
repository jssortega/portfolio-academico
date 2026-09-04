import 'dart:io';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:finance_tfg/modelo/modelo.dart';
import 'package:firebase_storage/firebase_storage.dart';

class FirebaseUsuarioDAO implements UsuarioDAO {

  @override
  Future<void> registrarUsuario(Usuario usuario, String contrasena) async {
    try{
      final credencial = await FirebaseAuth.instance.createUserWithEmailAndPassword(email: usuario.getEmail(), password: contrasena);

      String uid = credencial.user!.uid;

      await FirebaseFirestore.instance.collection('Usuario').doc(uid).set({
        'uid': uid,
        'nombre': usuario.getNombre(),
        'nombre_usuario': usuario.getNombreUsuario(),
        'email': usuario.getEmail()
      });
    }on FirebaseAuthException catch (e) {
      if (e.code == 'weak-password') {
        print('The password provided is too weak.');
      } else if (e.code == 'email-already-in-use') {
        print('The account already exists for that email.');
      }
    } catch (e){
      print(e);
    }

  }

  @override
  Future<void> inicioSesion(String email, String contrasena) async {
    try {
      await FirebaseAuth.instance.signInWithEmailAndPassword(email: email, password: contrasena);
    } on FirebaseAuthException catch (e) {
      if (e.code == 'user-not-found') {
        print('No user found for that email.');
      } else if (e.code == 'wrong-password') {
        print('Wrong password provided for that user.');
      }
    }
  }

  @override
  Future<void> cerrarSesion() async{
    try {
      await FirebaseAuth.instance.signOut();
    } catch (e) {
      print("Error al cerrar sesión: $e");
    }
  }


  @override
  String? getUidUsuarioActual() => FirebaseAuth.instance.currentUser?.uid;


  @override
  Stream<Usuario?> streamUsuario(String uid) {
    return FirebaseFirestore.instance.collection('Usuario').doc(uid).snapshots().map((doc) => doc.exists ? Usuario.fromMap(doc.data() as Map<String, dynamic>) : null);
  }

  @override
  Stream<List<UsuarioConRol>> getUsuariosCuentaActual(String idCuenta) {
    return FirebaseFirestore.instance.collection("Usuario_Cuenta").where("cuenta_id", isEqualTo: idCuenta).snapshots().asyncMap((snapshotRelacion) async {

      final List<String> idUsuarios = [];
      final Map<String, String> roles = {};

      for (var doc in snapshotRelacion.docs){
        final data = doc.data();
        final String usuarioId = data["usuario_id"];
        final String rol = data["rol"];

        idUsuarios.add(usuarioId);
        roles[usuarioId] = rol;
      }

      if (idUsuarios.isEmpty) {
        return <UsuarioConRol>[];
      }

      final snapshotUsuarios = await FirebaseFirestore.instance.collection("Usuario").where("uid", whereIn: idUsuarios).get();

      return snapshotUsuarios.docs.map((doc) {
        final usuario = Usuario.fromMap(doc.data());
        final String rol = roles[doc.id]!;
        return UsuarioConRol(usuario: usuario, rol: rol);
      }).toList();
    });
  }

  @override
  Future<void> modificarUsuario(String nombre, String nombreUsuario, String email, File? imagenPerfil, String? contrasenaActual) async{
    final uid = getUidUsuarioActual();
    User? user = FirebaseAuth.instance.currentUser;

    if (uid == null || user == null) {
      return;
    }

    DocumentReference usuarioRef = FirebaseFirestore.instance.collection('Usuario').doc(uid);

    try {

      if (email != user.email) {
        if (contrasenaActual == null || contrasenaActual.isEmpty) {
          throw FirebaseAuthException(
            code: 'requires-recent-login',
            message: 'Es necesario introducir tu contraseña actual para cambiar el correo.',
          );
        }

        AuthCredential credential = EmailAuthProvider.credential(
          email: user.email!,
          password: contrasenaActual,
        );

        await user.reauthenticateWithCredential(credential);
        await user.verifyBeforeUpdateEmail(email);
      }

      String? urlImagenPerfil;

      if (imagenPerfil != null) {
        final storageRef = FirebaseStorage.instance.ref().child('usuarios').child(uid).child('foto_perfil.jpg');

        final subidaImagen = await storageRef.putFile(imagenPerfil);

        urlImagenPerfil = await subidaImagen.ref.getDownloadURL();

      }

      await usuarioRef.update({
        'nombre': nombre,
        'nombre_usuario': nombreUsuario,
        'email': email,
        'imagen_perfil': urlImagenPerfil
      });

    } catch (e) {
      print("Error al actualizar usuario: $e");
    }
  }

  @override
  Future<Usuario?> buscarUsuarioPorUid(String uid) async {
    final doc = await FirebaseFirestore.instance.collection('Usuario').doc(uid).get();

    if(!doc.exists || doc.data() == null){
      return null;
    }

    return Usuario.fromMap(doc.data()!);
  }

  @override
  Future<List<Usuario>> buscarUsuariosPorNombre(String nombreUsuario) async {
    if (nombreUsuario.trim().length < 2) return [];

    final nombreUsuarioBusqueda = nombreUsuario.trim().toLowerCase();

    final snapshot = await FirebaseFirestore.instance.collection('Usuario')
        .where('nombre_usuario', isGreaterThanOrEqualTo: nombreUsuarioBusqueda)
        .where('nombre_usuario', isLessThanOrEqualTo: '$nombreUsuarioBusqueda\uf8ff')
        .limit(5)
        .get();

    return snapshot.docs.map((doc) => Usuario.fromMap(doc.data())).toList();
    
  }

  @override
  Future<void> eliminarUsuario(String uid, String contrasena) async{
    try {
      await FirebaseFirestore.instance.collection("Usuario").doc(uid).delete();

      final relaciones = await FirebaseFirestore.instance.collection("Usuario_Cuenta").where("usuario_id", isEqualTo: uid).get();

      for(var doc in relaciones.docs){
        await doc.reference.delete();
      }

      final User? user = FirebaseAuth.instance.currentUser;

      AuthCredential credential = EmailAuthProvider.credential(
          email: user!.email!,
          password: contrasena
      );

      await user.reauthenticateWithCredential(credential);

      await user.delete();

    } catch(e){
      print(e);
    }
  }
  
}