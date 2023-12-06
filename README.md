# Telegram PC Control Bot

This Python script serves as a Telegram bot for controlling and monitoring a Windows PC. It allows users to perform various actions, such as shutting down the computer, taking screenshots, terminating processes, opening URLs, and more. The bot also provides information about the PC's hardware, active processes, and system usage.
Features

Process Monitoring: The bot monitors the creation of new processes and logs when a user starts an application.
Remote Control: Users can perform actions like shutting down the PC, taking screenshots, and terminating processes remotely via Telegram commands.
PC Information: The bot provides detailed information about the connected PC, including processor details, RAM usage, disk information, network usage, and system uptime.
Interactive Process List: Users can view and navigate through a paginated list of active processes, including their names and memory usage.

## Installation and Configuration

Clone the repository to your local machine.

`git clone https://github.com/yourusername/telegram-pc-control-bot.git`

Install the required Python packages.

`pip install -r requirements.txt`

Edit a config.py file with your Telegram bot token (TOKEN) and authorized ID (AUTHORIZED_ID).

Run the script.

`python main.py`

## Telegram Commands

  - /start: Display a list of available commands.
   - /error {text}: Simulate a fake error message.
   - /screenshot`: Take a screenshot of the desktop.
   - /off: Shut down the computer.
   - /off_devices: Disable the keyboard and mouse until the next reboot.
   - /processes: View a list of active processes interactively.
   - /url {url}: Open the specified URL in the default web browser.
   - /terminate {process}: Terminate a specified process.
   - /open {program}: Open a specified program.
   - /pc: Display detailed information about the connected PC.
   - /stop: Stop the bot and exit the script.

### Contributions and Issues

__Feel free to contribute to the project by submitting pull requests or opening issues. If you encounter any problems or have suggestions for improvement, please let us know.__

###### Disclaimer

###### *This script is intended for educational purposes and should be used responsibly. The author is not responsible for any misuse or damage caused by using this script.*
