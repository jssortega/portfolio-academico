#ifndef __IGVESCENA3D
#define __IGVESCENA3D

#if defined(__APPLE__) && defined(__MACH__)
#include <GLUT/glut.h>
#include <OpenGL/gl.h>
#include <OpenGL/glu.h>
#else

#include <GL/glut.h>

#endif // defined(__APPLE__) && defined(__MACH__)

/**
 * Partes del modelo
 */
enum parte
{	basex   ///< Identifica la base del modelo
   , cuerpoinferior   ///< Identifica el angCuerpo inferior del modelo
   , cuerposuperior   ///< Identifica el angCuerpo superior del modelo
   , brazo   ///< Identifica el brazo del modelo
};

/**
 * Los objetos de esta clase representan escenas 3D para su visualizaci�n
 */
class igvEscena3D
{  private:
      // Atributos
	   // TODO: Apartado C: a�adir qu� los atributos para el control de los grados de libertad del modelo
       // Variables movimiento del cuerpo
       float angCuerpo = 0;

        //Variables movimiento piernas
        float giPierIzq = 0;
        float giPierDer = 0;

        //Variables para tirar el vaso
        float angVaso=0;

        //Varible para el movimiento del vaso en la animacion
        float movVaso = 0;

	   // Otros atributos
      bool ejes = true;   ///< Indica si hay que dibujar los ejes coordenados o no

   public:

      // Constructores por defecto y destructor
      igvEscena3D();
      ~igvEscena3D();

      // m�todo con las llamadas OpenGL para visualizar la escena
      void visualizar();

      // TODO: Apartado B: M�todos para visualizar cada parte del modelo


      // TODO: Apartado C: a�adir aqu� los m�todos para modificar los grados de libertad del modelo


      bool get_ejes ();
      void set_ejes ( bool _ejes );

    float getCuerpo() const;
    void setCuerpo(float cuerpo);

    float getGiPierIzq() const;
    void setGiPierIzq(float giPierIzq);
    float getGiPierDer() const;
    void setGiPierDer(float giPierDer);

    float getMovVaso() const;
    void setMovVaso(float movVaso);

    void setAngVaso(float angVaso);

private:
      void pintar_ejes ();

      void crearEscena();

};

#endif   // __IGVESCENA3D
