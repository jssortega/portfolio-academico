import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_es.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('es'),
  ];

  /// [InicioPantalla] Texto del botón para ocultar los importes y el saldo de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Ocultar saldo'**
  String get ocultarSaldo;

  /// [InicioPantalla] Texto del botón para mostrar los importes y el saldo de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Mostrar saldo'**
  String get mostrarSaldo;

  /// [CardSaldoActual] Texto para indicar el saldo que tiene la cuenta
  ///
  /// In es, this message translates to:
  /// **'Saldo actual'**
  String get saldoActual;

  /// [InicioPantalla] Texto para indicar los últimos movimientos de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Últimos movimientos'**
  String get ultimosMovimientos;

  /// [InicioPantalla] Texto del chip para filtrar todos los movimientos de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Todos'**
  String get todosChip;

  /// [InicioPantalla] Texto del chip para filtrar los movimientos fijos de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Fijos'**
  String get fijosChip;

  /// [InicioPantalla] Texto del chip para filtrar los movimientos que corresponden a ingresos de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Ingresos'**
  String get ingresosChip;

  /// [InicioPantalla] Texto del chip para filtrar los movimientos que corresponden a gastos de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Gastos'**
  String get gastosChip;

  /// [InicioPantalla] Texto del botón que lleva a mostrar todos los movimientos de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Mostrar más'**
  String get mostrarMas;

  /// [InicioPantalla] Texto del botón editar perfil del drawer
  ///
  /// In es, this message translates to:
  /// **'Editar perfil'**
  String get editarPerfilDrawer;

  /// [InicioPantalla] Texto para acceder a la pantalla de cuentas en el drawer
  ///
  /// In es, this message translates to:
  /// **'Cambiar cuenta'**
  String get cambiarCuentaDrawer;

  /// [InicioPantalla] Texto para acceder a la pantalla de editar cuenta en el drawer y encabezado de su propia pantalla
  ///
  /// In es, this message translates to:
  /// **'Editar cuenta'**
  String get editarCuenta;

  /// [InicioPantalla] Texto para acceder a la pantalla de gestionar usuarios en el drawer y encabezado de su propia pantalla
  ///
  /// In es, this message translates to:
  /// **'Gestionar usuarios'**
  String get gestionarUsuarios;

  /// [InicioPantalla] Texto para acceder a la pantalla de bandeja de entrada en el drawer y encabezado de su propia pantalla
  ///
  /// In es, this message translates to:
  /// **'Bandeja de entrada'**
  String get bandejaDeEntrada;

  /// [InicioPantalla] Texto para acceder a la pantalla de idioma y divisa en el drawer y encabezado de su propia pantalla
  ///
  /// In es, this message translates to:
  /// **'Idioma y divisa'**
  String get idiomaDivisa;

  /// [InicioPantalla] Texto del botón de cerrar sesión que se encuentra en el drawer
  ///
  /// In es, this message translates to:
  /// **'Cerrar sesión'**
  String get cerrarSesion;

  /// [Categoría] Texto de la categoría de ocio
  ///
  /// In es, this message translates to:
  /// **'Ocio'**
  String get ocioCategoria;

  /// No description provided for @trabajoCategoria.
  ///
  /// In es, this message translates to:
  /// **'Trabajo'**
  String get trabajoCategoria;

  /// [Categoría] Texto de la categoría de viaje
  ///
  /// In es, this message translates to:
  /// **'Viaje'**
  String get viajeCategoria;

  /// [Categoría] Texto de la categoría de hogar
  ///
  /// In es, this message translates to:
  /// **'Hogar'**
  String get hogarCategoria;

  /// [EditarPerfil] Texto que indica el campo del nombre del perfil
  ///
  /// In es, this message translates to:
  /// **'Nombre'**
  String get nombre;

  /// [EditarPerfil] Texto que indica el campo del nombre de usuario del perfil
  ///
  /// In es, this message translates to:
  /// **'Nombre de usuario'**
  String get nombreUsuario;

  /// [EditarPerfil] Texto que indica el campo del email del perfil
  ///
  /// In es, this message translates to:
  /// **'Email'**
  String get email;

  /// [EditarPerfil] Texto del botón para eliminar una cuenta de usuario
  ///
  /// In es, this message translates to:
  /// **'Eliminar cuenta'**
  String get eliminarCuenta;

  /// [Cuentas] Titulo del Appbar de la pantalla Cuentas
  ///
  /// In es, this message translates to:
  /// **'Cuentas'**
  String get cuentasTitulo;

  /// No description provided for @seleccioneCuenta.
  ///
  /// In es, this message translates to:
  /// **'Seleccione una cuenta'**
  String get seleccioneCuenta;

  /// [Cuentas] Texto del botón para crear una cuenta
  ///
  /// In es, this message translates to:
  /// **'Crear cuenta'**
  String get crearCuentaButtom;

  /// [Cuentas] Texto que se muestra cuando el usuario no tiene ninguna cuenta creada
  ///
  /// In es, this message translates to:
  /// **'Todavía no tienes cuentas creadas'**
  String get sinCuentas;

  /// [GestionUsuarios] Texto informativo que indica que se muestran los usuarios de una cuenta
  ///
  /// In es, this message translates to:
  /// **'Usuarios'**
  String get usuarios;

  /// [GestionarUsuarios] Texto del botón para añadir a un usuario
  ///
  /// In es, this message translates to:
  /// **'Añadir usuario'**
  String get aniadirUsuarioButtom;

  /// [Rol] Texto del rol administrador
  ///
  /// In es, this message translates to:
  /// **'Administrador'**
  String get administradorRol;

  /// [Rol] Texto del rol consultor
  ///
  /// In es, this message translates to:
  /// **'Consultor'**
  String get consultorRol;

  /// [AniadirCuentaPantalla] Título de la pantalla para crear una nueva cuenta
  ///
  /// In es, this message translates to:
  /// **'Añadir cuenta'**
  String get anadirCuenta;

  /// [AniadirCuentaPantalla] Etiqueta del campo donde se introduce el nombre de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Nombre de la cuenta'**
  String get nombreCuenta;

  /// [AniadirCuentaPantalla] Texto de ejemplo del campo de nombre de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Trabajo'**
  String get ejemploNombreCuentaTrabajo;

  /// [AniadirCuentaPantalla] Etiqueta del campo donde se introduce el saldo inicial de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Saldo inicial'**
  String get saldoInicial;

  /// [AnadirMovimientoPantalla] Título de la pantalla para añadir un nuevo movimiento
  ///
  /// In es, this message translates to:
  /// **'Añadir movimiento'**
  String get anadirMovimiento;

  /// [AnadirMovimientoPantalla] Etiqueta del selector para elegir si el movimiento es un gasto o un ingreso
  ///
  /// In es, this message translates to:
  /// **'Tipo:'**
  String get tipoMovimientoEtiqueta;

  /// [AnadirMovimientoPantalla] Opción del selector para indicar que el movimiento es un gasto
  ///
  /// In es, this message translates to:
  /// **'Gasto'**
  String get gastoSelector;

  /// [AnadirMovimientoPantalla] Opción del selector para indicar que el movimiento es un ingreso
  ///
  /// In es, this message translates to:
  /// **'Ingreso'**
  String get ingresoSelector;

  /// [AnadirMovimientoPantalla] Etiqueta del selector para elegir si el movimiento es único o recurrente
  ///
  /// In es, this message translates to:
  /// **'Recurrencia'**
  String get recurrenciaEtiqueta;

  /// [AnadirMovimientoPantalla] Opción del selector para indicar que el movimiento no se repite
  ///
  /// In es, this message translates to:
  /// **'Único'**
  String get unicoSelector;

  /// [AnadirMovimientoPantalla] Opción del selector para indicar que el movimiento se repite en el tiempo
  ///
  /// In es, this message translates to:
  /// **'Recurrente'**
  String get recurrenteSelector;

  /// [AnadirMovimientoPantalla] Etiqueta del menú desplegable para seleccionar la categoría del movimiento
  ///
  /// In es, this message translates to:
  /// **'Categoría:'**
  String get categoriaEtiqueta;

  /// [AnadirMovimientoPantalla] Texto que indica que se debe seleccionar la fecha de inicio de un movimiento recurrente
  ///
  /// In es, this message translates to:
  /// **'Seleccione una fecha de inicio'**
  String get seleccioneFechaInicio;

  /// [AnadirMovimientoPantalla] Texto que indica que se debe seleccionar la fecha del movimiento
  ///
  /// In es, this message translates to:
  /// **'Seleccione una fecha'**
  String get seleccioneFecha;

  /// [AnadirMovimientoPantalla] Texto del botón para añadir una fecha de finalización a un movimiento recurrente
  ///
  /// In es, this message translates to:
  /// **'+Añadir fecha fin'**
  String get anadirFechaFin;

  /// [AnadirMovimientoPantalla] Texto que indica que se debe seleccionar la frecuencia de repetición del movimiento
  ///
  /// In es, this message translates to:
  /// **'Seleccione recurrencia'**
  String get seleccioneRecurrencia;

  /// [AnadirMovimientoPantalla] Opción para indicar que el movimiento recurrente se repite diariamente
  ///
  /// In es, this message translates to:
  /// **'Diario'**
  String get diarioChip;

  /// [AnadirMovimientoPantalla] Opción para indicar que el movimiento recurrente se repite semanalmente
  ///
  /// In es, this message translates to:
  /// **'Semanal'**
  String get semanalChip;

  /// [AnadirMovimientoPantalla] Opción para indicar que el movimiento recurrente se repite mensualmente
  ///
  /// In es, this message translates to:
  /// **'Mensual'**
  String get mensualChip;

  /// [AnadirMovimientoPantalla] Opción para indicar que el movimiento recurrente se repite anualmente
  ///
  /// In es, this message translates to:
  /// **'Anual'**
  String get anualChip;

  /// [BandejaEntradaInvitacionesPantalla] Mensaje mostrado cuando ocurre un error al cargar las invitaciones
  ///
  /// In es, this message translates to:
  /// **'Error: {error}'**
  String errorConDetalle(String error);

  /// [BandejaEntradaInvitacionesPantalla] Mensaje mostrado cuando el usuario no tiene invitaciones pendientes
  ///
  /// In es, this message translates to:
  /// **'Todavía no tienes invitaciones pendientes.'**
  String get sinInvitacionesPendientes;

  /// [BandejaEntradaInvitacionesPantalla] Texto que indica que otro usuario ha invitado al usuario actual a una cuenta
  ///
  /// In es, this message translates to:
  /// **'Te ha invitado a la cuenta:'**
  String get invitacionCuentaTexto;

  /// [BandejaEntradaInvitacionesPantalla] Etiqueta que precede al rol asignado en una invitación
  ///
  /// In es, this message translates to:
  /// **'Con rol:'**
  String get conRolEtiqueta;

  /// [BandejaEntradaInvitacionesPantalla] Texto del botón para aceptar una invitación
  ///
  /// In es, this message translates to:
  /// **'Aceptar'**
  String get aceptarInvitacion;

  /// [BandejaEntradaInvitacionesPantalla] Texto del botón para rechazar una invitación
  ///
  /// In es, this message translates to:
  /// **'Rechazar'**
  String get rechazarInvitacion;

  /// [CuentasPantalla] Mensaje mostrado cuando ocurre un error al cargar las cuentas del usuario
  ///
  /// In es, this message translates to:
  /// **'Error al cargar cuentas'**
  String get errorCargarCuentas;

  /// [CuentasPantalla] Texto de la opción del menú para eliminar una cuenta
  ///
  /// In es, this message translates to:
  /// **'Eliminar'**
  String get eliminarCuentaMenu;

  /// [CuentasPantalla] Título del diálogo de confirmación para eliminar una cuenta
  ///
  /// In es, this message translates to:
  /// **'Eliminar cuenta'**
  String get eliminarCuentaTitulo;

  /// [CuentasPantalla] Mensaje del diálogo de confirmación antes de eliminar una cuenta
  ///
  /// In es, this message translates to:
  /// **'¿Estás seguro de realizar esta acción?'**
  String get confirmarEliminarCuenta;

  /// [CuentasPantalla] Texto del botón para cancelar la eliminación de una cuenta
  ///
  /// In es, this message translates to:
  /// **'Cancelar'**
  String get cancelarEliminarCuenta;

  /// [CuentasPantalla] Texto del botón para confirmar la eliminación de una cuenta
  ///
  /// In es, this message translates to:
  /// **'Aceptar'**
  String get aceptarEliminarCuenta;

  /// [DetalleMovimientoRecurrentePantalla] Etiqueta que muestra la categoría del movimiento recurrente
  ///
  /// In es, this message translates to:
  /// **'Categoría'**
  String get categoriaDetalleMovimiento;

  /// [DetalleMovimientoRecurrentePantalla] Etiqueta que muestra la frecuencia del movimiento recurrente
  ///
  /// In es, this message translates to:
  /// **'Frecuencia'**
  String get frecuenciaDetalleMovimiento;

  /// [DetalleMovimientoRecurrentePantalla] Etiqueta que muestra la próxima fecha del movimiento recurrente
  ///
  /// In es, this message translates to:
  /// **'Próximo'**
  String get proximoDetalleMovimiento;

  /// [DetalleMovimientoRecurrentePantalla] Etiqueta que indica la fecha de inicio del movimiento recurrente
  ///
  /// In es, this message translates to:
  /// **'Inicio'**
  String get inicioDetalleMovimiento;

  /// [DetalleMovimientoRecurrentePantalla] Etiqueta que indica la fecha de finalización o referencia del movimiento recurrente
  ///
  /// In es, this message translates to:
  /// **'Fecha'**
  String get fechaDetalleMovimiento;

  /// [EstadisticasPantalla] Título de la pantalla de estadísticas
  ///
  /// In es, this message translates to:
  /// **'Estadísticas'**
  String get estadisticasTitulo;

  /// [EstadisticasPantalla] Etiqueta de la sección que muestra el resumen económico del mes
  ///
  /// In es, this message translates to:
  /// **'Resumen del mes'**
  String get resumenMes;

  /// [EstadisticasPantalla] Etiqueta de la sección que muestra los gastos agrupados por categoría
  ///
  /// In es, this message translates to:
  /// **'Gastos por categoría'**
  String get gastosPorCategoria;

  /// [EditarPerfilPantalla] Título del diálogo que solicita la contraseña para confirmar el cambio de email
  ///
  /// In es, this message translates to:
  /// **'Confirmar cambio de email'**
  String get confirmarCambioEmailTitulo;

  /// [EditarPerfilPantalla] Texto del diálogo que pide al usuario introducir su contraseña actual
  ///
  /// In es, this message translates to:
  /// **'Introduce tu contraseña actual:'**
  String get introduceContrasenaActual;

  /// [EditarPerfilPantalla] Etiqueta del campo de contraseña
  ///
  /// In es, this message translates to:
  /// **'Contraseña'**
  String get contrasenaCampo;

  /// [EditarPerfilPantalla] Texto de ayuda del campo donde el usuario introduce su contraseña
  ///
  /// In es, this message translates to:
  /// **'Introduce tu contraseña'**
  String get introduceContrasenaHint;

  /// [EditarPerfilPantalla] Texto del botón para cancelar una acción
  ///
  /// In es, this message translates to:
  /// **'Cancelar'**
  String get cancelarBoton;

  /// [EditarPerfilPantalla] Texto del botón para confirmar una acción
  ///
  /// In es, this message translates to:
  /// **'Confirmar'**
  String get confirmarBoton;

  /// [EditarPerfilPantalla] Título del diálogo para eliminar la cuenta del usuario
  ///
  /// In es, this message translates to:
  /// **'Eliminar cuenta'**
  String get eliminarCuentaTituloPerfil;

  /// [EditarPerfilPantalla] Texto del botón para confirmar la eliminación de la cuenta
  ///
  /// In es, this message translates to:
  /// **'Eliminar'**
  String get eliminarBoton;

  /// [Rol] Explicación del rol administrador, indicando que tiene acceso completo a las finanzas y configuraciones
  ///
  /// In es, this message translates to:
  /// **'Acceso total a finanzas y configuraciones'**
  String get administradorRolExplicacion;

  /// [Rol] Explicación del rol consultor, indicando que solo puede consultar movimientos y estadísticas
  ///
  /// In es, this message translates to:
  /// **'Solo lectura de movimientos y estadísticas'**
  String get consultorRolExplicacion;

  /// [InvitarUsuarioPantalla] Título de la pantalla para invitar a otro usuario a una cuenta
  ///
  /// In es, this message translates to:
  /// **'Invitar usuario'**
  String get invitarUsuarioTitulo;

  /// [InvitarUsuarioPantalla] Etiqueta del campo donde se introduce el nombre de usuario a invitar
  ///
  /// In es, this message translates to:
  /// **'Nombre de usuario'**
  String get nombreUsuarioCampo;

  /// [InvitarUsuarioPantalla] Texto de ejemplo del campo para buscar un nombre de usuario
  ///
  /// In es, this message translates to:
  /// **'example_000'**
  String get ejemploNombreUsuario;

  /// [InvitarUsuarioPantalla] Etiqueta de la sección donde se selecciona el rol que tendrá el usuario invitado
  ///
  /// In es, this message translates to:
  /// **'Seleccione rol'**
  String get seleccioneRol;

  /// [InvitarUsuarioPantalla] Texto del botón para enviar una invitación a otro usuario
  ///
  /// In es, this message translates to:
  /// **'Invitar'**
  String get invitarBoton;

  /// [InvitarUsuarioPantalla] Mensaje mostrado cuando no se ha podido cargar el usuario actual
  ///
  /// In es, this message translates to:
  /// **'No se ha cargado el usuario actual'**
  String get usuarioActualNoCargado;

  /// [InvitarUsuarioPantalla] Mensaje mostrado cuando el usuario intenta invitar a alguien sin tener una cuenta seleccionada
  ///
  /// In es, this message translates to:
  /// **'No hay ninguna cuenta seleccionada'**
  String get sinCuentaSeleccionada;

  /// [InvitarUsuarioPantalla] Mensaje mostrado cuando el usuario intenta enviar una invitación sin seleccionar un usuario válido
  ///
  /// In es, this message translates to:
  /// **'Selecciona un usuario válido'**
  String get seleccionaUsuarioValido;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'es'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'es':
      return AppLocalizationsEs();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
