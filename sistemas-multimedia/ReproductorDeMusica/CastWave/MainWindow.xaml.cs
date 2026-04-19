using System;
using System.Windows.Threading;

namespace CastWave
{
    public partial class MainWindow
    {

        public MainWindow()
        {
            InitializeComponent();
            
            filePath = "grabacion.wav";

            // Método que llama al hacer click al botón de play/pausa de las canciones
            BtnPlayPause1.Click += BtnPlayPauseClick;
            BtnPlayPause2.Click += BtnPlayPauseClick;
            // Método que llama al hacer click a los pads
            pad_1.Click += BtnPads;
            pad_2.Click += BtnPads;
            pad_3.Click += BtnPads;
            pad_4.Click += BtnPads;
            pad_5.Click += BtnPads;
            pad_6.Click += BtnPads;
            
            // Método que llama al hacer click para seleccionar los micrófonos
            mic1.Click += mic_Click;
            mic2.Click += mic_Click;
            mic3.Click += mic_Click;
            mic4.Click += mic_Click;
            mic5.Click += mic_Click;
            
            // Método que llama al hacer click a los botones de mutear los micrófonos
            mute1.Click += mute_Click;
            mute2.Click += mute_Click;
            mute3.Click += mute_Click;
            mute4.Click += mute_Click;
            mute5.Click += mute_Click;
            
            // Método que llama al hacer click al botón para comenzar la grabación
            RecordButton.Click += RecordButton_Click;
            
            
            // Crear y configurar el DispatcherTimer
            timer = new DispatcherTimer();
            timer.Interval = TimeSpan.FromSeconds(1); // Actualizar cada segundo
            timer.Tick += Timer_Tick;
        }
        
    }
}