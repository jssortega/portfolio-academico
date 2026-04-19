using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Controls;

namespace CastWave
{
    public partial class MainWindow
    {
        private MediaPlayer mediaPlayerPads = new MediaPlayer();
        private void BtnPads(object sender, RoutedEventArgs e) {
            Button button = (Button)sender;

            // Verifica si el botón tiene un sonido asignado
            if (button.Tag == null || string.IsNullOrEmpty(button.Tag.ToString()))
            {
                // Si no tiene sonido asignado, abre una ventana para seleccionar un archivo
                var openFileDialog = new Microsoft.Win32.OpenFileDialog
                {
                    Filter = "Archivos MP3 (*.mp3)|*.mp3"
                };
                if (openFileDialog.ShowDialog() == true)
                {
                    // Asigna el archivo seleccionado al botón y almacena la ruta del archivo en la propiedad Tag del botón
                    button.Tag = openFileDialog.FileName;
                    // Actualiza el TextBlock para mostrar el nombre del archivo seleccionado sin la extensión
                    ((TextBlock)button.Content).Text = System.IO.Path.GetFileNameWithoutExtension(openFileDialog.FileName);
                    // Reproduce el sonido asociado al botón
                    mediaPlayerPads.Open(new Uri(openFileDialog.FileName));
                    mediaPlayerPads.Play();
                }
            }
            else
            {
                // Si el botón ya tiene un sonido asignado lo reproduce
                mediaPlayerPads.Open(new Uri(button.Tag.ToString()));
                mediaPlayerPads.Play();
            }
        }


    }
}