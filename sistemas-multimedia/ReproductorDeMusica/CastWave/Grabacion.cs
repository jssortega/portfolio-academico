using System.Windows;
using NAudio.Wave;

namespace CastWave
{
    public partial class MainWindow
    {

        private string filePath;
        

        // Métodos relacionados con la grabación de audio
        private void StartRecording()
        {
            waveSource = new WaveInEvent();
            waveSource.WaveFormat = new WaveFormat(44100, 1);
            waveSource.DataAvailable += WaveSourceDataAvailable;

            waveFile = new WaveFileWriter(filePath, waveSource.WaveFormat);

            waveSource.StartRecording();
        }

        private void StopRecording()
        {
            waveSource.StopRecording();
            waveSource.Dispose();
            waveFile.Close();
            waveFile.Dispose();
        }

        private void WaveSourceDataAvailable(object sender, WaveInEventArgs e)
        {
            // Verifica si el micrófono está muteado
            if (!IsAnyMicMuted())
            {
                waveFile.Write(e.Buffer, 0, e.BytesRecorded);
            }
        }

        private void RecordButton_Click(object sender, RoutedEventArgs e)
        {
            if (waveSource == null)
            {
                StartRecording();
                RecordButton.Content = "Detener";
            }
            else
            {
                StopRecording();
                RecordButton.Content = "Iniciar";
            }
        }
    }
}
