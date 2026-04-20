package com.mycompany.peliculas;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;

public class GestorIdiomas {
    private final Map<String, String[]> idiomas = new HashMap<>();
   
    
    public GestorIdiomas(String archivo) throws IOException {
        cargarIdiomas(archivo);
    }

    private void cargarIdiomas(String archivo) throws IOException {
        File archivoFile = new File(archivo);
        try (BufferedReader br = new BufferedReader(new FileReader(archivoFile))) {
        int numeroIdiomas = Integer.parseInt(br.readLine().trim());
        for (int i = 0; i < numeroIdiomas; i++) {
            String codigoIdioma = br.readLine().trim();
            int numeroCadenas = Integer.parseInt(br.readLine().trim());
            String[] cadenas = new String[numeroCadenas];
            for (int j = 0; j < numeroCadenas; j++) {
                cadenas[j] = br.readLine().trim();
            }

            int numeroImagenes = Integer.parseInt(br.readLine().trim());
            String[] imagenes = new String[numeroImagenes];
            for (int k = 0; k < numeroImagenes; k++) {
                imagenes[k] = br.readLine().trim();
            }

            String[] cadenasImagenes = new String[numeroCadenas + numeroImagenes];
            System.arraycopy(cadenas, 0, cadenasImagenes, 0, numeroCadenas);
            System.arraycopy(imagenes, 0, cadenasImagenes, numeroCadenas, numeroImagenes);

            idiomas.put(codigoIdioma, cadenasImagenes);
        }
    } catch (FileNotFoundException e) {
        throw new IOException("El archivo " + archivo + " no se encontró.", e);
    }
}


    public Map<String, String[]> getIdiomas() {
        return idiomas;
    }
    
}
