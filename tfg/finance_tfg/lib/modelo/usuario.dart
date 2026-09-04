class Usuario{
  String _uid = "";
  String _nombre = "";
  String _nombreUsuario = "";
  String _email = "";
  String _imagenPerfil = "";

  Usuario({String? uid, required String nombre, required String nombreUsuario, required String email, String? imagenPerfil}){
    _uid = uid ?? "";
    _nombre = nombre;
    _nombreUsuario = nombreUsuario;
    _email = email;
    _imagenPerfil = imagenPerfil ?? "";
  }

  String getUid(){
    return _uid;
  }

  String getNombre(){
    return _nombre;
  }
  
  String getNombreUsuario(){
    return _nombreUsuario;
  }
  
  String getEmail(){
    return _email;
  }

  String getImagenPerfil() {
    return _imagenPerfil;
  }


  factory Usuario.fromMap(Map<String, dynamic> data) {
    return Usuario(
      uid: data['uid'] ?? '',
      nombre: data['nombre'] ?? '',
      nombreUsuario: data['nombre_usuario'] ?? '',
      email: data['email'] ?? '',
      imagenPerfil: data['imagen_perfil'] ?? '',
    );
  }

}