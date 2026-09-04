// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Spanish Castilian (`es`).
class AppLocalizationsEs extends AppLocalizations {
  AppLocalizationsEs([String locale = 'es']) : super(locale);

  @override
  String get ocultarSaldo => 'Ocultar saldo';

  @override
  String get mostrarSaldo => 'Mostrar saldo';

  @override
  String get saldoActual => 'Saldo actual';

  @override
  String get ultimosMovimientos => 'Últimos movimientos';

  @override
  String get todosChip => 'Todos';

  @override
  String get fijosChip => 'Fijos';

  @override
  String get ingresosChip => 'Ingresos';

  @override
  String get gastosChip => 'Gastos';

  @override
  String get mostrarMas => 'Mostrar más';

  @override
  String get editarPerfilDrawer => 'Editar perfil';

  @override
  String get cambiarCuentaDrawer => 'Cambiar cuenta';

  @override
  String get editarCuenta => 'Editar cuenta';

  @override
  String get gestionarUsuarios => 'Gestionar usuarios';

  @override
  String get bandejaDeEntrada => 'Bandeja de entrada';

  @override
  String get idiomaDivisa => 'Idioma y divisa';

  @override
  String get cerrarSesion => 'Cerrar sesión';

  @override
  String get ocioCategoria => 'Ocio';

  @override
  String get trabajoCategoria => 'Trabajo';

  @override
  String get viajeCategoria => 'Viaje';

  @override
  String get hogarCategoria => 'Hogar';

  @override
  String get nombre => 'Nombre';

  @override
  String get nombreUsuario => 'Nombre de usuario';

  @override
  String get email => 'Email';

  @override
  String get eliminarCuenta => 'Eliminar cuenta';

  @override
  String get cuentasTitulo => 'Cuentas';

  @override
  String get seleccioneCuenta => 'Seleccione una cuenta';

  @override
  String get crearCuentaButtom => 'Crear cuenta';

  @override
  String get sinCuentas => 'Todavía no tienes cuentas creadas';

  @override
  String get usuarios => 'Usuarios';

  @override
  String get aniadirUsuarioButtom => 'Añadir usuario';

  @override
  String get administradorRol => 'Administrador';

  @override
  String get consultorRol => 'Consultor';

  @override
  String get anadirCuenta => 'Añadir cuenta';

  @override
  String get nombreCuenta => 'Nombre de la cuenta';

  @override
  String get ejemploNombreCuentaTrabajo => 'Trabajo';

  @override
  String get saldoInicial => 'Saldo inicial';

  @override
  String get anadirMovimiento => 'Añadir movimiento';

  @override
  String get tipoMovimientoEtiqueta => 'Tipo:';

  @override
  String get gastoSelector => 'Gasto';

  @override
  String get ingresoSelector => 'Ingreso';

  @override
  String get recurrenciaEtiqueta => 'Recurrencia';

  @override
  String get unicoSelector => 'Único';

  @override
  String get recurrenteSelector => 'Recurrente';

  @override
  String get categoriaEtiqueta => 'Categoría:';

  @override
  String get seleccioneFechaInicio => 'Seleccione una fecha de inicio';

  @override
  String get seleccioneFecha => 'Seleccione una fecha';

  @override
  String get anadirFechaFin => '+Añadir fecha fin';

  @override
  String get seleccioneRecurrencia => 'Seleccione recurrencia';

  @override
  String get diarioChip => 'Diario';

  @override
  String get semanalChip => 'Semanal';

  @override
  String get mensualChip => 'Mensual';

  @override
  String get anualChip => 'Anual';

  @override
  String errorConDetalle(String error) {
    return 'Error: $error';
  }

  @override
  String get sinInvitacionesPendientes =>
      'Todavía no tienes invitaciones pendientes.';

  @override
  String get invitacionCuentaTexto => 'Te ha invitado a la cuenta:';

  @override
  String get conRolEtiqueta => 'Con rol:';

  @override
  String get aceptarInvitacion => 'Aceptar';

  @override
  String get rechazarInvitacion => 'Rechazar';

  @override
  String get errorCargarCuentas => 'Error al cargar cuentas';

  @override
  String get eliminarCuentaMenu => 'Eliminar';

  @override
  String get eliminarCuentaTitulo => 'Eliminar cuenta';

  @override
  String get confirmarEliminarCuenta =>
      '¿Estás seguro de realizar esta acción?';

  @override
  String get cancelarEliminarCuenta => 'Cancelar';

  @override
  String get aceptarEliminarCuenta => 'Aceptar';

  @override
  String get categoriaDetalleMovimiento => 'Categoría';

  @override
  String get frecuenciaDetalleMovimiento => 'Frecuencia';

  @override
  String get proximoDetalleMovimiento => 'Próximo';

  @override
  String get inicioDetalleMovimiento => 'Inicio';

  @override
  String get fechaDetalleMovimiento => 'Fecha';

  @override
  String get estadisticasTitulo => 'Estadísticas';

  @override
  String get resumenMes => 'Resumen del mes';

  @override
  String get gastosPorCategoria => 'Gastos por categoría';

  @override
  String get confirmarCambioEmailTitulo => 'Confirmar cambio de email';

  @override
  String get introduceContrasenaActual => 'Introduce tu contraseña actual:';

  @override
  String get contrasenaCampo => 'Contraseña';

  @override
  String get introduceContrasenaHint => 'Introduce tu contraseña';

  @override
  String get cancelarBoton => 'Cancelar';

  @override
  String get confirmarBoton => 'Confirmar';

  @override
  String get eliminarCuentaTituloPerfil => 'Eliminar cuenta';

  @override
  String get eliminarBoton => 'Eliminar';

  @override
  String get administradorRolExplicacion =>
      'Acceso total a finanzas y configuraciones';

  @override
  String get consultorRolExplicacion =>
      'Solo lectura de movimientos y estadísticas';

  @override
  String get invitarUsuarioTitulo => 'Invitar usuario';

  @override
  String get nombreUsuarioCampo => 'Nombre de usuario';

  @override
  String get ejemploNombreUsuario => 'example_000';

  @override
  String get seleccioneRol => 'Seleccione rol';

  @override
  String get invitarBoton => 'Invitar';

  @override
  String get usuarioActualNoCargado => 'No se ha cargado el usuario actual';

  @override
  String get sinCuentaSeleccionada => 'No hay ninguna cuenta seleccionada';

  @override
  String get seleccionaUsuarioValido => 'Selecciona un usuario válido';
}
