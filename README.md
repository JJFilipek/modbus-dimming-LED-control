# Modbus Control Application

A simple GUI application for controlling Modbus devices. This tool allows you to interact with Modbus slaves, enabling the reading and writing of registers via a user-friendly interface. Designed for educational, testing, and demonstration purposes, it showcases basic Modbus TCP communication within a Python application.

## Features

- **Connection Management**: Connect to a Modbus server using a specified IP address.
- **Slave Interaction**: Selectively apply a percentage value to individual or all connected Modbus slave devices.
- **User Feedback**: Dynamically highlight the selected slave device in the GUI.
- **Error Handling**: Manage connection issues and validate user input effectively.

## Prerequisites

Before you begin, ensure you have met the following requirements:
- Python 3.x installed on your system.
- pymodbus library installed. You can install it via pip:

```
pip install pymodbus
```

## Installation

Clone this repository to your local machine or download the source code:

```
git clone https://github.com/JJFilipek/Modbus_dimming_LED_control
```

## Usage

To use the Modbus Control Application, follow these steps:

1. Run the application with Python:

```
python main.py
```

2. Enter the IP address of your Modbus server in the application window.
3. Select a slave device to interact with from the list.
4. Enter a percentage value to apply to the selected slave or all slaves.
5. Click "Apply" to send the command to the selected slave, or "Apply to All" to broadcast the command to all slaves.

## Customization

You can customize the application to fit your specific setup by modifying the `slave_names` list and the default Modbus server IP address within the source code.

## Contributing

Contributions to the Modbus Control Application are welcome. Please fork the repository and create a pull request with your improvements.

## License

This project is licensed under the MIT License - see the LICENSE file in the repository for details.

## Acknowledgments

- Thanks to the pymodbus library for providing a comprehensive Modbus communication solution.
- This project was inspired by the need for a simple, educational tool for understanding Modbus protocols.

