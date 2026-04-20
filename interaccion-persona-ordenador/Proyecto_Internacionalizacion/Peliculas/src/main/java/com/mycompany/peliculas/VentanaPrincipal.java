/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/GUIForms/JFrame.java to edit this template
 */
package com.mycompany.peliculas;

import java.io.IOException;
import java.util.Map;
import javax.swing.*;

/**
 *
 * @author jortega
 */
public class VentanaPrincipal extends javax.swing.JFrame {
    public static String obtenerClavePorValor(Map<String, String> mapa, String valor) {
        for (Map.Entry<String, String> entrada : mapa.entrySet()) {
            if (entrada.getValue().equals(valor)) {
                return entrada.getKey();
            }
        }
        return null;
    }
    
    private GestorIdiomas gestorIdiomas;
    private String idiomaActual = "es";
    VentanaAñadir ventanaAñadir = new VentanaAñadir();
    VentanaConsultar ventanaConsultar = new VentanaConsultar();
    VentanaEliminar ventanaEliminar = new VentanaEliminar();
    VentanaModificar ventanaModificar = new VentanaModificar();
    
    private void cargarIdiomasDesplegable() {
        String nombreIdioma;
        for(String codigo : gestorIdiomas.getIdiomas().keySet()){
            nombreIdioma = gestorIdiomas.getIdiomas().get(codigo)[0];
            
            JMenuItem itemIdioma = new JMenuItem(nombreIdioma);
            String[] textos = gestorIdiomas.getIdiomas().get(codigo);
            ImageIcon bandera = new ImageIcon(getClass().getResource(textos[31]));
            itemIdioma.setIcon(bandera);
            idiomasMenu.add(itemIdioma);
            
            itemIdioma.addActionListener(evt -> {
                idiomaActual = codigo;
                actualizarTexto();
            });
            
            
            
        }
        
    }
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        principalDestockPanel = new javax.swing.JDesktopPane();
        principalFrame = new javax.swing.JInternalFrame();
        imagenIdioma = new javax.swing.JLabel();
        mensajeBienvenida = new javax.swing.JLabel();
        jMenuBar2 = new javax.swing.JMenuBar();
        funcionesMenu = new javax.swing.JMenu();
        añadirMenu = new javax.swing.JMenuItem();
        eliminarMenu = new javax.swing.JMenuItem();
        consultarMenu = new javax.swing.JMenuItem();
        modificarMenu = new javax.swing.JMenuItem();
        opcionesMenu = new javax.swing.JMenu();
        idiomasMenu = new javax.swing.JMenu();

        setDefaultCloseOperation(javax.swing.WindowConstants.EXIT_ON_CLOSE);

        principalFrame.setClosable(true);
        principalFrame.setToolTipText("");
        principalFrame.setVisible(true);

        imagenIdioma.setMaximumSize(new java.awt.Dimension(1000, 1000));
        imagenIdioma.setPreferredSize(new java.awt.Dimension(500, 250));

        mensajeBienvenida.setHorizontalAlignment(javax.swing.SwingConstants.CENTER);
        mensajeBienvenida.setText("Bienvendido a la aplicación de gestión de películas");
        mensajeBienvenida.setHorizontalTextPosition(javax.swing.SwingConstants.CENTER);
        mensajeBienvenida.setPreferredSize(new java.awt.Dimension(400, 18));

        jMenuBar2.setMinimumSize(new java.awt.Dimension(154, 150));

        funcionesMenu.setText("Funciones");
        funcionesMenu.setMinimumSize(new java.awt.Dimension(100, 100));

        añadirMenu.setText("Añadir");
        añadirMenu.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                añadirMenuActionPerformed(evt);
            }
        });
        funcionesMenu.add(añadirMenu);

        eliminarMenu.setText("Eliminar");
        eliminarMenu.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                eliminarMenuActionPerformed(evt);
            }
        });
        funcionesMenu.add(eliminarMenu);

        consultarMenu.setText("Consulta");
        consultarMenu.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                consultarMenuActionPerformed(evt);
            }
        });
        funcionesMenu.add(consultarMenu);

        modificarMenu.setText("Modificar");
        modificarMenu.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                modificarMenuActionPerformed(evt);
            }
        });
        funcionesMenu.add(modificarMenu);

        jMenuBar2.add(funcionesMenu);

        opcionesMenu.setText("Editar");

        idiomasMenu.setText("idiomas");
        opcionesMenu.add(idiomasMenu);

        jMenuBar2.add(opcionesMenu);

        principalFrame.setJMenuBar(jMenuBar2);

        javax.swing.GroupLayout principalFrameLayout = new javax.swing.GroupLayout(principalFrame.getContentPane());
        principalFrame.getContentPane().setLayout(principalFrameLayout);
        principalFrameLayout.setHorizontalGroup(
            principalFrameLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(principalFrameLayout.createSequentialGroup()
                .addGroup(principalFrameLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addGroup(principalFrameLayout.createSequentialGroup()
                        .addGap(72, 72, 72)
                        .addComponent(mensajeBienvenida, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE))
                    .addGroup(principalFrameLayout.createSequentialGroup()
                        .addGap(22, 22, 22)
                        .addComponent(imagenIdioma, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)))
                .addContainerGap(22, Short.MAX_VALUE))
        );
        principalFrameLayout.setVerticalGroup(
            principalFrameLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(principalFrameLayout.createSequentialGroup()
                .addGap(28, 28, 28)
                .addComponent(imagenIdioma, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addGap(45, 45, 45)
                .addComponent(mensajeBienvenida, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addContainerGap(61, Short.MAX_VALUE))
        );

        principalDestockPanel.setLayer(principalFrame, javax.swing.JLayeredPane.DEFAULT_LAYER);

        javax.swing.GroupLayout principalDestockPanelLayout = new javax.swing.GroupLayout(principalDestockPanel);
        principalDestockPanel.setLayout(principalDestockPanelLayout);
        principalDestockPanelLayout.setHorizontalGroup(
            principalDestockPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addComponent(principalFrame)
        );
        principalDestockPanelLayout.setVerticalGroup(
            principalDestockPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addComponent(principalFrame)
        );

        javax.swing.GroupLayout layout = new javax.swing.GroupLayout(getContentPane());
        getContentPane().setLayout(layout);
        layout.setHorizontalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(javax.swing.GroupLayout.Alignment.TRAILING, layout.createSequentialGroup()
                .addContainerGap()
                .addComponent(principalDestockPanel)
                .addContainerGap())
        );
        layout.setVerticalGroup(
            layout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addContainerGap()
                .addComponent(principalDestockPanel))
        );

        pack();
    }// </editor-fold>//GEN-END:initComponents

    private void consultarMenuActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_consultarMenuActionPerformed
        actualizarTexto();
        ventanaConsultar.setLocationRelativeTo(this);
        ventanaConsultar.setVisible(true);
    }//GEN-LAST:event_consultarMenuActionPerformed

    private void añadirMenuActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_añadirMenuActionPerformed
        ventanaAñadir.setLocationRelativeTo(this);
        ventanaAñadir.setVisible(true);
    }//GEN-LAST:event_añadirMenuActionPerformed

    private void eliminarMenuActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_eliminarMenuActionPerformed
        ventanaEliminar.setLocationRelativeTo(this);
        ventanaEliminar.setVisible(true);
    }//GEN-LAST:event_eliminarMenuActionPerformed

    private void modificarMenuActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_modificarMenuActionPerformed
        ventanaModificar.setLocationRelativeTo(this);
        ventanaModificar.setVisible(true);
    }//GEN-LAST:event_modificarMenuActionPerformed

    


    public VentanaPrincipal() {
    try {
        gestorIdiomas = new GestorIdiomas("idiomas.tsv");
        initComponents();
        cargarIdiomasDesplegable();
        actualizarTexto();
    } catch (IOException e) {
        System.exit(1);
    }
}



    private void actualizarTexto() {
        String[] textos = gestorIdiomas.getIdiomas().get(idiomaActual);
        if (textos != null) {
            principalFrame.setTitle(textos[1]);
            funcionesMenu.setText(textos[2]); // Funciones
            opcionesMenu.setText(textos[3]); // Editar
            idiomasMenu.setText(textos[4]); //Idioma
            añadirMenu.setText(textos[5]); // Añadir
            eliminarMenu.setText(textos[6]); // Eliminar
            consultarMenu.setText(textos[7]); // Consultar
            modificarMenu.setText(textos[8]); //Modificar
            mensajeBienvenida.setText(textos[9]); //Mensaje bienvenida
            ImageIcon fondo = new ImageIcon(getClass().getResource(textos[30]));
            imagenIdioma.setIcon(fondo); //Imagen fondo
            
            ventanaAñadir.setTituloVentana(textos[5]);
            ventanaAñadir.setTituloLabel(textos[10]);
            ventanaAñadir.setAñoLabel(textos[11]);
            ventanaAñadir.setDirectorLabel(textos[12]);
            ventanaAñadir.setAñadirButton(textos[5]);
            ventanaAñadir.setprimaryKeyDialog(textos[13], textos[14],textos[29]);
            ventanaAñadir.setemptyPanelDialog(textos[15], textos[14],textos[28]);
            ventanaAñadir.setInformationPanelDialog(textos[16], textos[14],textos[27]);
            
            ventanaEliminar.setTituloVentana(textos[6]);
            ventanaEliminar.setInfoLabel(textos[17]);
            ventanaEliminar.setEliminarButton(textos[6]);
            ventanaEliminar.setEliminadaDialog(textos[18],textos[14], textos[27]); 
            ventanaEliminar.setnoExisteDialog(textos[19],textos[14], textos[29]);
            ventanaEliminar.setEmptyDialog(textos[20],textos[14], textos[28]);
            
            ventanaConsultar.setTituloVentana(textos[7]);
            ventanaConsultar.consultarElementosArchivo("datos.tsv", textos[10], textos[11], textos[12]);
            
            ventanaModificar.setTituloVentana(textos[8]);
            ventanaModificar.setBuscarLabel(textos[21]);
            ventanaModificar.setBuscarButton(textos[22]);
            ventanaModificar.setEmptyDialog(textos[20],textos[14], textos[28]);
            ventanaModificar.setNoExisteDialog(textos[19],textos[14], textos[29]);
            
            ventanaModificar.setAplicarLabels(textos[23], textos[24], textos[25]);
            ventanaModificar.setAplicarButton(textos[26]);
            ventanaModificar.setAplicarEmptyDialog(textos[15], textos[14],textos[28]);
        }
    }
    
    public String getIdiomaActual(){
        return idiomaActual;
    }

    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JMenuItem añadirMenu;
    private javax.swing.JMenuItem consultarMenu;
    private javax.swing.JMenuItem eliminarMenu;
    private javax.swing.JMenu funcionesMenu;
    private javax.swing.JMenu idiomasMenu;
    private javax.swing.JLabel imagenIdioma;
    private javax.swing.JMenuBar jMenuBar2;
    private javax.swing.JLabel mensajeBienvenida;
    private javax.swing.JMenuItem modificarMenu;
    private javax.swing.JMenu opcionesMenu;
    private javax.swing.JDesktopPane principalDestockPanel;
    private javax.swing.JInternalFrame principalFrame;
    // End of variables declaration//GEN-END:variables
}
