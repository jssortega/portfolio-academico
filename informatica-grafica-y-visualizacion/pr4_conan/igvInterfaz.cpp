#include <cstdlib>
#include <stdio.h>

#include "igvInterfaz.h"

// Aplicaci�n del patr�n de dise�o Singleton
igvInterfaz *igvInterfaz::_instancia = nullptr;

// M�todos p�blicos ----------------------------------------

/**
 * M�todo para acceder al objeto �nico de la clase, en aplicaci�n del patr�n de
 * dise�o Singleton
 * @return Una referencia al objeto �nico de la clase
 */
igvInterfaz &igvInterfaz::getInstancia ()
{  if ( !_instancia )
   {  _instancia = new igvInterfaz;
   }

   return *_instancia;
}

/**
 * Crea el mundo que se visualiza en la ventana
 */
void igvInterfaz::crear_mundo ()
{  // inicia la c�mara
   _instancia->camara.set ( IGV_PARALELA, { 6.0, 4.0, 8 }, { 0, 0, 0 }
                            , { 0, 1.0, 0 }, -1 * 4.5, 1 * 4.5, -1 * 4.5, 1 * 4.5
                            , 1, 200 );
}

/**
 * Inicializa todos los par�metros para crear una ventana de visualizaci�n
 * @param argc N�mero de par�metros por l�nea de comandos al ejecutar la
 *             aplicaci�n
 * @param argv Par�metros por l�nea de comandos al ejecutar la aplicaci�n
 * @param _ancho_ventana Ancho inicial de la ventana de visualizaci�n
 * @param _alto_ventana Alto inicial de la ventana de visualizaci�n
 * @param _pos_X Coordenada X de la posici�n inicial de la ventana de
 *               visualizaci�n
 * @param _pos_Y Coordenada Y de la posici�n inicial de la ventana de
 *               visualizaci�n
 * @param _titulo T�tulo de la ventana de visualizaci�n
 * @pre Se asume que todos los par�metros tienen valores v�lidos
 * @post Cambia el alto y ancho de ventana almacenado en el objeto
 */
void igvInterfaz::configura_entorno ( int argc, char **argv, int _ancho_ventana
                                      , int _alto_ventana, int _pos_X, int _pos_Y
                                      , std::string _titulo )
{  // inicializaci�n de las variables de la interfaz
   ancho_ventana = _ancho_ventana;
   alto_ventana = _alto_ventana;

   // inicializaci�n de la ventana de visualizaci�n
   glutInit ( &argc, argv );
   glutInitDisplayMode ( GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH );
   glutInitWindowSize ( _ancho_ventana, _alto_ventana );
   glutInitWindowPosition ( _pos_X, _pos_Y );
   glutCreateWindow ( _titulo.c_str () );

   glEnable ( GL_DEPTH_TEST ); // activa el ocultamiento de superficies por z-buffer
   glClearColor ( 1.0, 1.0, 1.0, 0.0 ); // establece el color de fondo de la ventana

   glEnable ( GL_LIGHTING ); // activa la iluminacion de la escena
   glEnable ( GL_NORMALIZE ); // normaliza los vectores normales para calculo iluminacion

   glEnable ( GL_TEXTURE_2D ); // activa el uso de texturas

   crear_mundo (); // crea el mundo a visualizar en la ventana
}

/**
 * M�todo para visualizar la escena y esperar a eventos sobre la interfaz
 */
void igvInterfaz::inicia_bucle_visualizacion ()
{  glutMainLoop (); // inicia el bucle de visualizaci�n de GLUT
}

/**
 * M�todo para el control de eventos de teclado producidos exclusivamente
 * por las teclas de funci�n (F1...F12) y de direcci�n (flechas, insert, avanzar
 * y retroceder p�gina, e inicio y fin)
 * @param key C�digo que identifica a la tecla pulsada
 * @param x Coordenada X de la posici�n del cursor en la ventana al pulsar la
 *        tecla
 * @param y Coordenada Y de la posici�n del cursor en la ventana al pulsar la
 *        tecla
 */
void igvInterfaz::specialFunc ( int key, int x, int y )
{  // TODO: Apartado E: manejo de las teclas especiales del teclado para mover la posici�n del foco


   glutPostRedisplay (); // renueva el contenido de la ventana de vision
}

/**
 * M�todo para control de eventos del teclado
 * @param key C�digo de la tecla pulsada
 * @param x Coordenada X de la posici�n del cursor del rat�n en el momento del
 *          evento de teclado
 * @param y Coordenada Y de la posici�n del cursor del rat�n en el momento del
 *          evento de teclado
 * @pre Se asume que todos los par�metros tienen valores v�lidos
 * @post Los atributos de la clase pueden cambiar, dependiendo de la tecla pulsada
 */
void igvInterfaz::keyboardFunc ( unsigned char key, int x, int y )
{  switch ( key )
   {  case 'd':
       _instancia->escena.setCoefDifusoR(_instancia->escena.getCoefDifusoR() + 0.1);
       break;
       case 'D':
           _instancia->escena.setCoefDifusoR(_instancia->escena.getCoefDifusoR() - 0.1);
           break;
       case 's':
           _instancia->escena.setCoefEspecularR(_instancia->escena.getCoefEspecularR() + 0.1);
           break;
       case 'S':
           _instancia->escena.setCoefEspecularR(_instancia->escena.getCoefEspecularR() - 0.1);
           break;
       case 'p':
           _instancia->escena.setExpPhong(_instancia->escena.getExpPhong() + 10.0);
           break;
       case 'P':
           _instancia->escena.setExpPhong(_instancia->escena.getExpPhong() - 10.0);
           break;
      case 'e': // activa/desactiva la visualizaci�n de los ejes
         _instancia->escena.set_ejes ( !_instancia->escena.get_ejes () );
         break;
         case '8': // Tecla de flecha arriba
           _instancia->foco.getPosicion()[1] += 0.2;

           break;
       case '2': // Tecla de flecha abajo
           _instancia->foco.getPosicion()[1] -= 0.2;
           break;
       case '6': // Tecla de flecha derecha
           _instancia->foco.getPosicion()[0] += 0.2;
           break;
       case '4': // Tecla de flecha izquierda
           _instancia->foco.getPosicion()[0] -= 0.2;
           break;
      case 27: // tecla de escape para SALIR
         exit ( 1 );
         break;
   }
   glutPostRedisplay (); // renueva el contenido de la ventana de vision
}

/**
 * M�todo que define la c�mara de visi�n y el viewport. Se llama autom�ticamente
 * cuando se cambia el tama�o de la ventana.
 * @param w Nuevo ancho de la ventana
 * @param h Nuevo alto de la ventana
 * @pre Se asume que todos los par�metros tienen valores v�lidos
 */
void igvInterfaz::reshapeFunc ( int w, int h )
{  // dimensiona el viewport al nuevo ancho y alto de la ventana
   // guardamos valores nuevos de la ventana de visualizaci�n
   _instancia->set_ancho_ventana ( w );
   _instancia->set_alto_ventana ( h );

   // establece los par�metros de la c�mara y de la proyecci�n
   _instancia->camara.aplicar ();
}

/**
 * M�todo para visualizar la escena
 */
void igvInterfaz::displayFunc ()
{  glClear ( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT ); // borra la ventana y el z-buffer

   // se establece el viewport
   glViewport ( 0, 0, _instancia->get_ancho_ventana (), _instancia->get_alto_ventana () );

   // establece los par�metros de la c�mara y de la proyecci�n
   _instancia->camara.aplicar ();

   //visualiza la escena
   _instancia->escena.visualizar ();

   // refresca la ventana
   glutSwapBuffers (); // se utiliza, en vez de glFlush(), para evitar el parpadeo
}

/**
 * M�todo para inicializar los callbacks GLUT
 */
void igvInterfaz::inicializa_callbacks ()
{  glutKeyboardFunc ( keyboardFunc );
   glutReshapeFunc ( reshapeFunc );
   glutDisplayFunc ( displayFunc );
   glutSpecialFunc ( specialFunc );
}

/**
 * M�todo para consultar el ancho de la ventana de visualizaci�n
 * @return El valor almacenado como ancho de la ventana de visualizaci�n
 */
int igvInterfaz::get_ancho_ventana ()
{  return ancho_ventana;
}

/**
 * M�todo para consultar el alto de la ventana de visualizaci�n
 * @return El valor almacenado como alto de la ventana de visualizaci�n
 */
int igvInterfaz::get_alto_ventana ()
{  return alto_ventana;
}

/**
 * M�todo para cambiar el ancho de la ventana de visualizaci�n
 * @param _ancho_ventana Nuevo valor para el ancho de la ventana de visualizaci�n
 * @pre Se asume que el par�metro tiene un valor v�lido
 * @post El ancho de ventana almacenado en la aplicaci�n cambia al nuevo valor
 */
void igvInterfaz::set_ancho_ventana ( int _ancho_ventana )
{  ancho_ventana = _ancho_ventana;
}

/**
 * M�todo para cambiar el alto de la ventana de visualizaci�n
 * @param _alto_ventana Nuevo valor para el alto de la ventana de visualizaci�n
 * @pre Se asume que el par�metro tiene un valor v�lido
 * @post El alto de ventana almacenado en la aplicaci�n cambia al nuevo valor
 */
void igvInterfaz::set_alto_ventana ( int _alto_ventana )
{  alto_ventana = _alto_ventana;
}
