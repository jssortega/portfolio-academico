import 'package:finance_tfg/modelo/modelo.dart';

abstract class InviatacionDao{
  Future<void> crearInvitacion(Invitacion invitacion);

  Stream<List<Invitacion>> getInvitacionesPendientes(String uid);

  Future<void> aceptarInvitacion(String invitacionId);

  Future<void> rechazarInvitacion(String invitacionId);
}