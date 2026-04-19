using System;
using System.Windows;
using NAudio.Wave;
using System.Collections.Generic;
using System.Linq;
using System.Windows.Controls;
using System.Windows.Media;
using NAudio.CoreAudioApi;

namespace CastWave
{
    public partial class MainWindow
    {
        private WaveInEvent waveSource;
        private WaveFileWriter waveFile;
        private Dictionary<string, string> micDevices = new Dictionary<string, string>();
        private Dictionary<string, bool> micMuteStates = new Dictionary<string, bool>
        {
            { "mic1", false },
            { "mic2", false },
            { "mic3", false },
            { "mic4", false },
            { "mic5", false }
        };
        
        private bool IsAnyMicMuted()
        {
            return micMuteStates.Values.Any(muted => muted);
        }

        

        private void mic_Click(object sender, RoutedEventArgs e)
        {
            // Obtiene el botón clicado
            Button clickedButton = sender as Button;
            if (clickedButton == null) return;

            // Obtiene la lista de dispositivos de entrada de audio
            MMDeviceEnumerator enumerator = new MMDeviceEnumerator();
            MMDeviceCollection devices = enumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
            if (devices.Count > 0)
            {
                // Crea una ventana para seleccionar el dispositivo
                var deviceSelector = new ComboBox
                {
                    ItemsSource = devices,
                    SelectedIndex = 0, // Selecciona el primer dispositivo por defecto
                    Width = 500,
                    HorizontalContentAlignment = HorizontalAlignment.Left
                };

                
                var dialog = new Window
                {
                    Title = "Seleccionar Dispositivo de Audio",
                    Content = deviceSelector,
                    Width = 500,
                    Height = 100,
                    ResizeMode = ResizeMode.NoResize,
                    WindowStartupLocation = WindowStartupLocation.CenterOwner,
                    Owner = this
                };

                dialog.ShowDialog();

                // Accede al dispositivo seleccionado
                if (deviceSelector.SelectedItem != null)
                {
                    string selectedDevice = deviceSelector.SelectedItem.ToString().Trim();
                    
                    // Asigna el dispositivo seleccionado al micrófono correspondiente
                    micDevices[clickedButton.Name] = selectedDevice;

                    // Muestra un mensaje por pantalla
                    MessageBox.Show($"Dispositivo seleccionado para {clickedButton.Name}: {selectedDevice}");
                }

            }
            else
            {
                MessageBox.Show("No se encontraron dispositivos de entrada de audio.");
            }
        }




        private void mute_Click(object sender, RoutedEventArgs e)
        {
            // Obtien el botón clicado
            Button clickedButton = sender as Button;
            if (clickedButton == null) return;

            // Alterna el estado de mute
            string buttonName = clickedButton.Name.Replace("mute", "mic");
            bool isMuted = micMuteStates[buttonName];
            micMuteStates[buttonName] = !isMuted;

            if (micMuteStates[buttonName])
            {
                clickedButton.Content = "Unmute";
                clickedButton.Background = Brushes.Red;
            }
            else
            {
                clickedButton.Content = "Mute";
                clickedButton.Background = Brushes.Orange;
            }
        }

        private string GetMicButtonName(string controlName)
        {
            switch (controlName)
            {
                case "mute1":
                case "volume1": return "mic1";
                case "mute2":
                case "volume2": return "mic2";
                case "mute3":
                case "volume3": return "mic3";
                case "mute4":
                case "volume4": return "mic4";
                case "mute5":
                case "volume5": return "mic5";
                default: return null;
            }
        }
        
        private void volume_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            // Obtiene el Slider clicado
            Slider volumeSlider = sender as Slider;
            if (volumeSlider == null) return;

            // Obtiene el nombre del botón de micrófono asociado
            string sliderName = volumeSlider.Name;
            string micButtonName = GetMicButtonName(sliderName);

            if (micButtonName != null && micDevices.ContainsKey(micButtonName))
            {
                string selectedDevice = micDevices[micButtonName];
                double volume = volumeSlider.Value;
                
                SetMicrophoneVolume(selectedDevice, volume);
            }
        }



        private void SetMicrophoneVolume(string deviceName, double volume)
        {
            // Obtiene el dispositivo de audio correspondiente al nombre
            MMDeviceEnumerator enumerator = new MMDeviceEnumerator();
            MMDeviceCollection devices = enumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
            MMDevice device = devices.FirstOrDefault(d => string.Equals(d.FriendlyName.Trim(), deviceName.Trim(), StringComparison.OrdinalIgnoreCase));

            if (device != null)
            {
                // Convierte el volumen de un rango de 0 a 100 a un rango de 0 a 1
                float newVolume = (float)(volume / 100.0);

                // Ajusta el volumen del dispositivo
                device.AudioEndpointVolume.MasterVolumeLevelScalar = newVolume;
            }
            else
            {
                MessageBox.Show("No se encontró el dispositivo de audio especificado.");
            }
        }


        }
    }

