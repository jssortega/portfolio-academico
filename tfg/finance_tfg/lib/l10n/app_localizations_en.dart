// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get ocultarSaldo => 'Hide balance';

  @override
  String get mostrarSaldo => 'Show balance';

  @override
  String get saldoActual => 'Current balance';

  @override
  String get ultimosMovimientos => 'Last transactions';

  @override
  String get todosChip => 'All';

  @override
  String get fijosChip => 'Fixed';

  @override
  String get ingresosChip => 'Revenue';

  @override
  String get gastosChip => 'Expenses';

  @override
  String get mostrarMas => 'Show more';

  @override
  String get editarPerfilDrawer => 'Edit profile';

  @override
  String get cambiarCuentaDrawer => 'Switch accounts';

  @override
  String get editarCuenta => 'Edit account';

  @override
  String get gestionarUsuarios => 'Manage users';

  @override
  String get bandejaDeEntrada => 'Inbox';

  @override
  String get idiomaDivisa => 'Language and currency';

  @override
  String get cerrarSesion => 'Sign out';

  @override
  String get ocioCategoria => 'Leisure';

  @override
  String get trabajoCategoria => 'Work';

  @override
  String get viajeCategoria => 'Travel';

  @override
  String get hogarCategoria => 'Home';

  @override
  String get nombre => 'Name';

  @override
  String get nombreUsuario => 'Username';

  @override
  String get email => 'Email';

  @override
  String get eliminarCuenta => 'Delete account';

  @override
  String get cuentasTitulo => 'Accounts';

  @override
  String get seleccioneCuenta => 'Select an account';

  @override
  String get crearCuentaButtom => 'Create an account';

  @override
  String get sinCuentas => 'You haven\'t created any accounts yet';

  @override
  String get usuarios => 'Users';

  @override
  String get aniadirUsuarioButtom => 'Add user';

  @override
  String get administradorRol => 'Administrator';

  @override
  String get consultorRol => 'Consultant';

  @override
  String get anadirCuenta => 'Add account';

  @override
  String get nombreCuenta => 'Account name';

  @override
  String get ejemploNombreCuentaTrabajo => 'Work';

  @override
  String get saldoInicial => 'Initial balance';

  @override
  String get anadirMovimiento => 'Add transaction';

  @override
  String get tipoMovimientoEtiqueta => 'Type:';

  @override
  String get gastoSelector => 'Expense';

  @override
  String get ingresoSelector => 'Income';

  @override
  String get recurrenciaEtiqueta => 'Recurrence';

  @override
  String get unicoSelector => 'One-time';

  @override
  String get recurrenteSelector => 'Recurring';

  @override
  String get categoriaEtiqueta => 'Category:';

  @override
  String get seleccioneFechaInicio => 'Select a start date';

  @override
  String get seleccioneFecha => 'Select a date';

  @override
  String get anadirFechaFin => '+Add end date';

  @override
  String get seleccioneRecurrencia => 'Select recurrence';

  @override
  String get diarioChip => 'Daily';

  @override
  String get semanalChip => 'Weekly';

  @override
  String get mensualChip => 'Monthly';

  @override
  String get anualChip => 'Yearly';

  @override
  String errorConDetalle(String error) {
    return 'Error: $error';
  }

  @override
  String get sinInvitacionesPendientes =>
      'You don\'t have any pending invitations yet.';

  @override
  String get invitacionCuentaTexto => 'Invited you to the account:';

  @override
  String get conRolEtiqueta => 'With role:';

  @override
  String get aceptarInvitacion => 'Accept';

  @override
  String get rechazarInvitacion => 'Reject';

  @override
  String get errorCargarCuentas => 'Error loading accounts';

  @override
  String get eliminarCuentaMenu => 'Delete';

  @override
  String get eliminarCuentaTitulo => 'Delete account';

  @override
  String get confirmarEliminarCuenta =>
      'Are you sure you want to perform this action?';

  @override
  String get cancelarEliminarCuenta => 'Cancel';

  @override
  String get aceptarEliminarCuenta => 'Accept';

  @override
  String get categoriaDetalleMovimiento => 'Category';

  @override
  String get frecuenciaDetalleMovimiento => 'Frequency';

  @override
  String get proximoDetalleMovimiento => 'Next';

  @override
  String get inicioDetalleMovimiento => 'Start';

  @override
  String get fechaDetalleMovimiento => 'Date';

  @override
  String get estadisticasTitulo => 'Statistics';

  @override
  String get resumenMes => 'Monthly summary';

  @override
  String get gastosPorCategoria => 'Expenses by category';

  @override
  String get confirmarCambioEmailTitulo => 'Confirm email change';

  @override
  String get introduceContrasenaActual => 'Enter your current password:';

  @override
  String get contrasenaCampo => 'Password';

  @override
  String get introduceContrasenaHint => 'Enter your password';

  @override
  String get cancelarBoton => 'Cancel';

  @override
  String get confirmarBoton => 'Confirm';

  @override
  String get eliminarCuentaTituloPerfil => 'Delete account';

  @override
  String get eliminarBoton => 'Delete';

  @override
  String get administradorRolExplicacion =>
      'Full access to finances and settings';

  @override
  String get consultorRolExplicacion =>
      'Read-only access to transactions and statistics';

  @override
  String get invitarUsuarioTitulo => 'Invite user';

  @override
  String get nombreUsuarioCampo => 'Username';

  @override
  String get ejemploNombreUsuario => 'example_000';

  @override
  String get seleccioneRol => 'Select role';

  @override
  String get invitarBoton => 'Invite';

  @override
  String get usuarioActualNoCargado => 'The current user has not been loaded';

  @override
  String get sinCuentaSeleccionada => 'No account is selected';

  @override
  String get seleccionaUsuarioValido => 'Select a valid user';
}
