using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using System.ServiceProcess;

namespace BotService
{
    public partial class Service1 : ServiceBase
    {

        private Process _process;

        protected override void OnStart(string[] args)
        {
            base.OnStart(args);

            // Start the first Python script
            var startInfo1 = new ProcessStartInfo
            {
                FileName = @"C:\Program Files\Python37\python.exe",
                Arguments = @"C:\Users\Administrator\brdybot\brdybot.py",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true
            };

            _process = Process.Start(startInfo1);

        }

        protected override void OnStop()
        {
            base.OnStop();

            // Stop the Python scripts
            _process?.Kill();
        }

        protected override void OnShutdown()
        {
            base.OnShutdown();

            // Stop the Python scripts
            _process?.Kill();
        }

        private void InitializeComponent()
        {
            // 
            // Service1
            // 
            this.ServiceName = "BotService";

        }
    }
}
