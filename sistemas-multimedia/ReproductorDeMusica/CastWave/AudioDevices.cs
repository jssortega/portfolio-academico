using System;
using System.Runtime.InteropServices;
using System.Windows;
using System.Collections.Generic;

namespace CastWave
{
    public class AudioDevices
    {
        [DllImport("winmm.dll")]
        private static extern int waveInGetNumDevs();

        [DllImport("winmm.dll", CharSet = CharSet.Auto)]
        private static extern int waveInGetDevCaps(int uDeviceID, ref WAVEINCAPS pwic, int cbwic);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        private struct WAVEINCAPS
        {
            public short wMid;
            public short wPid;
            public int vDriverVersion;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
            public string szPname;
            public uint dwFormats;
            public short wChannels;
            public short wReserved1;
        }

        public static List<string> GetInputDevices()
        {
            List<string> devices = new List<string>();
            int waveInDevices = waveInGetNumDevs();
            WAVEINCAPS caps = new WAVEINCAPS();

            for (int i = 0; i < waveInDevices; i++)
            {
                if (waveInGetDevCaps(i, ref caps, Marshal.SizeOf(caps)) == 0)
                {
                    devices.Add(caps.szPname);
                }
            }

            return devices;
        }
    }

}