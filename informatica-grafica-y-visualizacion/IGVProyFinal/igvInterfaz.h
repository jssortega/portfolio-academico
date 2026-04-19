#ifndef __IGVINTERFAZ
#define __IGVINTERFAZ

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif   // defined(__APPLE__) && defined(__MACH__)

#include <string>

#include "igvEscena3D.h"
#include "igvCamara.h"

enum modoInterfaz
{  IGV_VISUALIZAR ///< En la ventana se va a visualizar de manera normal la escena
    , IGV_SELECCIONAR /**< Se ha hecho clic en la ventana de visualizaci�n, y la
                      *   escena se debe visualizar en modo selecci�n
                      */
};

/**
 * Los objetos de esta clase encapsulan la interfaz y el estado de la aplicaci�n
 */
class igvInterfaz
{  private:
      // Atributos
      int ancho_ventana = 0; ///< Ancho de la ventana de visualizaci�n
      int alto_ventana = 0;  ///< Alto de la ventana de visualizaci�n

      igvEscena3D escena; ///< Escena que se visualiza en la ventana definida por igvInterfaz
      igvCamara camara; ///< C�mara que se utiliza para visualizar la escena
      igvMallaTriangulos malla; ///< Malla de triangulos que construye los objetos de la escena

      static igvInterfaz* _instancia; ///< Direcci�n de memoria del objeto �nico de la clase

      /// Constructor por defecto
      igvInterfaz () = default;

      int cambioVista=0; ///< Entero para cambiar la vista

      igvPunto3D p0 = { 0, 0, 0 } ///< Posición de la cámara
        , r = { 0, 0, 0 } ///< Punto de referencia para las vistas
        , V = { 0, 0, 0 } ///< Vector que indica la vertical en la vista
        ;

    bool revertirCorrer=false; ///< Booleano utilizado para mover las piernas en direcciones contrarias en keyboardfunc()

    // Atributos para la seleccion de objetos
    modoInterfaz modo = IGV_VISUALIZAR; ///< Modo de visualizaci�n de la escena
    float cursorX = 0  /**< Coordenada X. Pixel de la pantalla sobre el que
                        *   esta situado el raton, para pulsar o arrastrar
                        */
    , cursorY = 0; /**< Coordenada Y. Pixel de la pantalla sobre el que
                      *   est� situado el raton, para pulsar o arrastrar
                      */
    float cursorXX = 0  /**< Coordenada X. Diferencia entre cuando se hace click
                        * por última vez y por primera vez
                        */;

    int objeto_seleccionado = -1; ///< Identificador del objeto seleccionado, -1 si no hay ninguno

    //Atributos utilizados para para la animación
    bool animacion = false; ///< Indica cuando tiene que empezar la animación
    int contadorAnimación = 0;
    int estado = 0; ///< Cambia entre las distintas escenas que se dan en la animación
    int tiempo = 400;

public:
      // Aplicaci�n del patr�n de dise�o Singleton
      static igvInterfaz& getInstancia ();

      /// Destructor
      ~igvInterfaz () = default;

      // M�todos est�ticos
      // callbacks de eventos
      // callbacks de eventos
      static void keyboardFunc ( unsigned char key, int x, int y ); // m�todo para control de eventos del teclado
      static void reshapeFunc ( int w, int h ); // m�todo que define la camara de vision y el viewport

      // se llama autom�ticamente cuando se cambia el tama�o de la ventana
      static void displayFunc (); // m�todo para visualizar la escena

    static void mouseFunc ( GLint boton, GLint estado, GLint x, GLint y ); // control de pulsacion del raton
    static void motionFunc ( GLint x, GLint y ); // control del desplazamiento del raton con boton pulsado

    static void idleFunc (); // m�todo para animar la escena

      // Metodos
      // crea el mundo que se visualiza en la ventana
      void crear_mundo ();

      // inicializa todos los par�metros para crear una ventana de visualizaci�n
      void configura_entorno ( int argc, char **argv // par�metros del main
                             , int _ancho_ventana, int _alto_ventana // ancho y alto de la ventana de visualizaci�n
                             , int _pos_X, int _pos_Y // posici�n inicial de la ventana de visualizaci�n
                             , std::string _titulo // t�tulo de la ventana de visualizaci�n
                             );
      void inicializa_callbacks (); // inicializa todos los callbacks

      void inicia_bucle_visualizacion (); // visualiza la escena y espera a eventos sobre la interfaz

      // m�todos get_ y set_ de acceso a los atributos
      int get_ancho_ventana ();

      int get_alto_ventana ();

      void set_ancho_ventana ( int _ancho_ventana );

      void set_alto_ventana ( int _alto_ventana );

      bool comparaColor(float color1, float color2, int precision);
};

#endif   // __IGVINTERFAZ
