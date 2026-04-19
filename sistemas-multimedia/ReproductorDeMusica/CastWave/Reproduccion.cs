using System;
using System.Windows;
using System.Windows.Media;
using System.Windows.Threading;
using System.Windows.Media.Imaging;
using System.IO;

namespace CastWave
{
    public partial class MainWindow
    {
        private MediaPlayer mediaPlayer = new MediaPlayer();
        private bool isPlaying = false;
        private DispatcherTimer timer;
        private string[] audioFiles;
        private int currentSongIndex = 0;
        private bool cambio = false;
        
        //Método que controla el evento al hacer click en el botón de play/pausa
         private void BtnPlayPauseClick(object sender, RoutedEventArgs e)
        {
            if (!isPlaying)
            {
                if (mediaPlayer.Source == null)
                {
                    SelectSong();
                }
                else
                {
                    PlaySong(currentSongIndex);
                }
            }
            else
            {
                PauseSong();
            }
        }
        
        //Método para reproducir la canción
        private void PlaySong(int index)
        {
            try
            {
                mediaPlayer.Play();
                isPlaying = true;
                if (!cambio)
                {
                    BtnPlayPause1.Content = "Pausa";
                    BtnPlayPause2.Content = "Play";
                }
                else
                {
                    BtnPlayPause1.Content = "Play";
                    BtnPlayPause2.Content = "Pausa";
                    
                }

                // Iniciar el temporizador
                timer.Start();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error al reproducir la canción: " + ex.Message);
            }
        }

        //Método para pausar la canción
        private void PauseSong()
        {
            try
            {
                mediaPlayer.Pause();
                isPlaying = false;
                // Comprueba que lado está reproduciendo para cambiar el botón que corresponda.
                if (!cambio)
                {
                    BtnPlayPause1.Content = "Play";
                }
                else
                {
                    BtnPlayPause2.Content = "Play";
                }

                // Se detiene el temporizador
                timer.Stop();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error al pausar la canción: " + ex.Message);
            }
        }
        
        //Abre una ventana emergente para seleccionar la cancion a reproducir
        private void SelectSong()
        {
            try
            {
                var openFileDialog = new Microsoft.Win32.OpenFileDialog();
                openFileDialog.Filter = "Archivos de audio|*.mp3;*.wav";
                if (openFileDialog.ShowDialog() == true)
                {
                    string directory = Path.GetDirectoryName(openFileDialog.FileName);
                    audioFiles = Directory.GetFiles(directory, "*.mp3"); // Obtener todos los archivos .mp3 en el directorio

                    // Obtiene el índice de la canción seleccionada
                    currentSongIndex = Array.IndexOf(audioFiles, openFileDialog.FileName);

                    // Reproduce la canción seleccionada
                    mediaPlayer.Open(new Uri(audioFiles[currentSongIndex]));
                    PlaySong(currentSongIndex);

                    // Obtiene y muestra los datos de la canción
                    cambio = false;
                    UpdateSongInfo(openFileDialog.FileName);
                    
                    UpdateSongInfo2(audioFiles[currentSongIndex+1]);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error al seleccionar la canción: " + ex.Message);
            }
        }

        private void Timer_Tick(object sender, EventArgs e)
        {
            if (mediaPlayer.NaturalDuration.HasTimeSpan)
            {
                double totalSeconds = mediaPlayer.NaturalDuration.TimeSpan.TotalSeconds;
                double currentPosition = mediaPlayer.Position.TotalSeconds;

                // Actualiza la barra de progreso calculando el porcentaje de progreso que lleva la canción
                if (!cambio)
                {
                    ProgressBar.Value = (currentPosition / totalSeconds) * 100;
                    ProgressBar2.Value = 0;
                }
                else
                {
                    ProgressBar.Value = 0;
                    ProgressBar2.Value = (currentPosition / totalSeconds) * 100;
                }

                // Verifica si la canción ha terminado
                if (currentPosition >= totalSeconds)
                {
                    NextSong();
                }
            }
        }

        private void NextSong()
        {
            cambio = !cambio;
            // Aumenta el índice de la canción actual
            currentSongIndex++;

            // Verifica si hemos llegado al final de la lista de canciones
            if (currentSongIndex >= audioFiles.Length)
            {
                currentSongIndex = 0; // Volver al principio de la lista
            }

            // Reproduce la siguiente canción
            mediaPlayer.Open(new Uri(audioFiles[currentSongIndex]));
            PlaySong(currentSongIndex);
            if (cambio)
            {
                // Obtiene y muestra los datos de la siguiente canción
                UpdateSongInfo(audioFiles[currentSongIndex+1]);
            }
            else
            {
                UpdateSongInfo2(audioFiles[currentSongIndex+1]); 
            }
        }

        private void UpdateSongInfo(string filePath)
        {
            // Obtiene el título de la canción y el artista.
            var file = TagLib.File.Create(filePath);
            string title = file.Tag.Title;
            TxtSongName.Text = title;
            string artist = file.Tag.FirstPerformer;
            TxtArtist.Text = artist;
            if (file.Tag.Pictures.Length > 0)
            {
                var bin = (byte[])(file.Tag.Pictures[0].Data.Data);
                var bitmap = new BitmapImage();
                bitmap.BeginInit();
                bitmap.StreamSource = new MemoryStream(bin);
                bitmap.EndInit();
                ImgSong.Source = bitmap;
            }
            else
            {
                // Si no hay imagen coge una por defecto
                ImgSong.Source = new BitmapImage(new Uri("/DefaultSong.png"));
            }
            file.Dispose();
        }
        
        private void UpdateSongInfo2(string filePath)
        {
            // Obtener el título de la canción y el artista.
            var file = TagLib.File.Create(filePath);
            string title = file.Tag.Title;
            TxtSongName2.Text = title;
            string artist = file.Tag.FirstPerformer;
            TxtArtist2.Text = artist;
            if (file.Tag.Pictures.Length > 0)
            {
                var bin = (byte[])(file.Tag.Pictures[0].Data.Data);
                var bitmap = new BitmapImage();
                bitmap.BeginInit();
                bitmap.StreamSource = new MemoryStream(bin);
                bitmap.EndInit();
                ImgSong2.Source = bitmap;
            }
            else
            {
                // Si no hay imagen coge una por defecto
                ImgSong2.Source = new BitmapImage(new Uri("/DefaultSong.png"));
            }

            // Cerrar el archivo después de obtener los metadatos
            file.Dispose();
        }
        
        private void VolumeSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            if (!cambio)
            {
                if (mediaPlayer != null)
                {
                    mediaPlayer.Volume = VolumeSlider.Value;
                }
            }
            else
            {
                if (mediaPlayer != null)
                {
                    mediaPlayer.Volume = VolumeSlider2.Value;
                }
            }
        }
    }
}