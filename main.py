import tkinter as tk
from tkinter import messagebox
from pymodbus.client import ModbusTcpClient
from pymodbus.transaction import ModbusSocketFramer
import pymodbus.exceptions
import requests
from functools import lru_cache
import threading
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# noinspection PyTypeChecker
class ModbusApp:
    def __init__(self):
        # Initialize main window settings and Modbus connection parameters
        self.top = tk.Tk()
        self.top.title("Modbus Automate")
        self.top.geometry("450x460")

        self.mydata = "192.168.0.1"  # use here your modbus module IP address
        self.mflux = 1000  # default flux value
        self.slave_address = None
        self.total_slaves = 8
        self.modbus_status = [False] * self.total_slaves
        self.slave_names = ["Module 5", "Module 6", "Module 7", "Module 8",
                            "Module 1", "Module 3", "Module 4", "Module 2"]
        self.slaves_display_order = [2, 0, 5, 4, 3, 1, 6, 7]
        self.power_update_timer = None
        self.auto_control = False
        self.auto_control_counter = 0
        self.counter_label = None
        self.auto_dimming_button = None

        self.client = None  # Initialize the Modbus client at class level
        self.setup_modbus_client()

        # Set up the Whatsapp parameters
        self.phone = "+48123456789"  # use here your phone number
        self.text = "Power guardian reduced brightness by 10%"  # your message
        self.api_key = "1234567"  # use here your API key

        # UI elements references
        self.button_references = []
        self.dot_references = []
        self.percentage_labels = []
        self.power_labels = []

        # Set up the GUI components
        self.setup_gui()

    def __del__(self):
        # Close Modbus connection when the application is closing.
        self.client.close()

    def setup_modbus_client(self):
        """
        Initializes and connects the Modbus TCP client.
        Establishes connection using predefined settings and handles connection errors.
        """
        self.client = ModbusTcpClient(self.mydata, port=502, framer=ModbusSocketFramer)
        if not self.client.connect():
            messagebox.showerror("Connection error", "The connection to the modules cannot be established. "
                                                     "Verify that you are connected to the local network, or  "
                                                     "your VPN is enabled.")
        else:
            logging.info("Connection to Modbus client established.")

    def close_modbus_client(self):
        # Close modbus connection
        if self.client:
            self.client.close()
            logging.info("Modbus client connection closed.")

    def set_slave_address(self, address, button=None):
        # Set the current slave address and update UI.
        self.slave_address = address
        if button:
            self.update_button_colors(button)
        self.update_dot_colors()
        logging.info(f"Module address set to {self.slave_address}")

    def update_button_colors(self, active_button):
        # Update the color of slave buttons to indicate the current selection.
        for btn in self.button_references:
            btn.config(bg='SystemButtonFace')
        if active_button:
            active_button.config(bg='light gray')

    @staticmethod
    def handle_modbus_error(exception, operation="operation"):
        """
        Handles exceptions from Modbus operations, logs the error, and shows a user-friendly message.
        Parameters:
        exception (Exception): The caught exception.
        operation (str): Description of the operation during which the error occurred.
        """
        logging.error(f"Modbus {operation} failed: {exception}")
        messagebox.showerror("Modbus error", f"An error occurred during {operation}.")

    # noinspection PyGlobalUndefined
    def run_sync_simple_client(self, comm, host, port, my_address, my_slave, my_value):
        # Executes a synchronous Modbus operation: read and write registers on the specified slave.
        try:
            if not self.client:
                self.setup_modbus_client()  # Setup client if not already set
            logging.info(f"Attempting {comm} connection to {host}:{port}")
            rr = self.client.read_holding_registers(address=132, count=1, slave=my_slave)
            if rr.isError():
                raise pymodbus.exceptions.ModbusException(rr.message)
            self.client.write_registers(address=my_address, values=[my_value], slave=my_slave)
            logging.info(f"Received data: {rr.registers}, Sent data: {my_value}")
            return True
        except (pymodbus.exceptions.ConnectionException, pymodbus.exceptions.ModbusException) as exc:
            messagebox.showerror("Modbus Error", str(exc))
            return False

    def read_holding_registers(self, address, count, slave_id):
        # Read specified holding registers from the selected slave device.
        try:
            response = self.client.read_holding_registers(address, count, unit=slave_id)
            if not response.isError():
                return response.registers
            else:
                raise pymodbus.exceptions.ModbusException(response)
        except (pymodbus.exceptions.ConnectionException, pymodbus.exceptions.ModbusException) as e:
            messagebox.showerror("Modbus Error", f"Error reading registers: {e}")
            return None

    def apply_percentage(self, percentage):
        # Apply percentage to the currently selected slave
        if self.slave_address is None:
            messagebox.showinfo("Slave not selected",
                                "Please select a block before applying the percentage value.")
            return False
        try:
            percentage_val = int(percentage)
            if percentage_val < 0 or percentage_val > 100:
                messagebox.showerror("Incorrect input data", "The value must be between 0 and 100.")
                return False

            # Find the index in the slave_address_mapping that matches the slave_address
            index = self.slaves_display_order.index(self.slave_address - 1)
            if index is None:
                messagebox.showerror("Error", "Incorrect slave address.")
                return False

            flux = int(percentage_val * self.mflux / 100)
            success = self.run_sync_simple_client("tcp", self.mydata, "502", 25,
                                                  self.slave_address, 1)
            if success:
                success = self.run_sync_simple_client("tcp", self.mydata, "502", 38,
                                                      self.slave_address, flux)
                if success:
                    # Update the corresponding percentage label by using the index found above

                    # Register responsible for read actual percentage from modbus module
                    # percentage_reg = client.read_holding_registers(address=256, count=1, slave=self.slave_address)
                    electric_power_fom_luminaires = self.client.read_holding_registers(address=257, count=1,
                                                                                       slave=self.slave_address)
                    dimmable_fixed_spectrum_luminaires = self.client.read_holding_registers(address=258, count=1,
                                                                                            slave=self.slave_address)
                    self.modbus_status[self.slave_address - 1] = True
                    self.percentage_labels[index].config(text=f"{percentage}%")
                    logging.info(f"Set to {percentage}% for slave {self.slave_address}")

                    self.power_labels[index].config(
                        text=f"{(electric_power_fom_luminaires.registers[0] * 65.536) + dimmable_fixed_spectrum_luminaires.registers[0]} W")
            else:
                self.modbus_status[self.slave_address - 1] = False
            self.update_dot_colors()
            return success
        except ValueError:
            messagebox.showerror("Incorrect input data", "The value must be between 0 and 100.")
            return False

    def apply_percentage_to_all(self, percentage):
        # Apply a given percentage to all slaves
        logging.info(f"Set up {percentage}% for all slaves")
        for i in range(self.total_slaves):
            self.set_slave_address(i + 1, None)
            success = self.apply_percentage(percentage)
            if not success:
                messagebox.showerror("Connection error", f"Error at {i + 1} slave. Aborting the operation.")
                break

    def close_selected_connection(self):
        # Send a command to disable modbus mode to the current slave
        logging.info(f"Closing connection with {self.slave_address} slave")
        self.run_sync_simple_client("tcp", self.mydata, "502", 25, self.slave_address, 0)
        self.modbus_status[self.slave_address - 1] = False
        self.update_dot_colors()

    def update_dot_colors(self):
        # Update dot colors based on the modbus_status, but according to the display order
        for i, dot in enumerate(self.dot_references):
            status_index = self.slaves_display_order[i]
            color = 'green' if self.modbus_status[status_index] else 'red'
            dot.config(fg=color)
        logging.info("Dott color update")

    def update_power_display(self):
        # Update the display of power readings from each slave.
        try:
            for i, slave_id in enumerate(self.slaves_display_order, start=1):
                # Ensuring use of the persistent client instead of creating a new one
                high_word = self.read_holding_registers(257, 1, slave_id=slave_id)
                low_word = self.read_holding_registers(258, 1, slave_id=slave_id)
                if high_word is not None and low_word is not None:
                    high_word_value = high_word[0]
                    low_word_value = low_word[0]
                    power = (high_word_value << 16) | low_word_value
                    self.power_labels[i - 1].config(text=f"{power} W")  # Adjusted index for labels
                else:
                    self.power_labels[i - 1].config(text="Read error")
        except Exception as e:
            messagebox.showerror("Error", f"Error updating power display: {e}")

    def on_close(self):
        # Attempt to close all connections gracefully on application close
        logging.info("Program shutdown...")
        connection_errors = False
        for addr in range(1, self.total_slaves + 1):
            success = self.run_sync_simple_client("tcp", self.mydata, "502", 25, addr, 0)
            if not success:
                connection_errors = True
                break
        if connection_errors:
            messagebox.showerror("Connection error", "The program cannot be closed successfully.")
        else:
            logging.info("All connections closed successfully.")
        if self.power_update_timer:
            self.power_update_timer.cancel()
        self.top.destroy()

    def setup_gui(self):
        # Set up the GUI layout
        tk.Label(self.top, text="Select slave", font="Courier 10").pack(pady=10)
        self.create_slave_buttons()
        self.setup_control_buttons()
        self.top.protocol("WM_DELETE_WINDOW", self.on_close)
        self.counter_label = tk.Label(self.top, text="Number of automatic executions: 0")
        self.counter_label.pack()

    def create_slave_buttons(self):
        # Create buttons at the top od the program
        master_frame = tk.Frame(self.top, bg="#e0e9d8")
        master_frame.pack(pady=10)
        left_frame = tk.Frame(master_frame, bg="#e0e9d8")
        left_frame.pack(side=tk.LEFT, padx=5)
        right_frame = tk.Frame(master_frame, bg="#e0e9d8")
        right_frame.pack(side=tk.LEFT, padx=5)
        self.power_labels = []

        halfway_point = len(self.slaves_display_order) // 2
        slave_address_mapping = [3, 1, 6, 5, 4, 2, 7, 8]  # customize your display order

        for i, display_index in enumerate(self.slaves_display_order):
            name = self.slave_names[display_index]
            is_left_side = i < halfway_point
            target_frame = left_frame if is_left_side else right_frame
            row_frame = tk.Frame(target_frame, bg="#e0e9d8")
            row_frame.pack(fill=tk.X, padx=5, pady=2)

            # Set up the grid with 2 columns
            row_frame.columnconfigure(0, weight=1)
            row_frame.columnconfigure(1, weight=1)

            button = tk.Button(row_frame, text=name, width=20)
            dot = tk.Label(row_frame, text="●", fg='red', font=('Helvetica', 14), bg="#e0e9d8")
            power = tk.Label(row_frame, text="--- W", fg='red', bg="#e0e9d8")
            percentage = tk.Label(row_frame, text="0%", fg='blue', bg="#e0e9d8")
            slave_address = slave_address_mapping[i]
            button.configure(command=lambda addr=slave_address, btn=button: self.set_slave_address(addr, btn))

            if is_left_side:
                # Place the dot on the left, button on the right
                dot.grid(row=0, column=2, sticky="e")
                percentage.grid(row=0, column=1, sticky="e")
                button.grid(row=0, column=0, sticky="w")
                power.grid(row=1, column=0, columnspan=2, sticky="s")

            else:
                # Place the button on the left, dot on the right

                dot.grid(row=0, column=0, sticky="e")
                percentage.grid(row=0, column=1, sticky="e")
                button.grid(row=0, column=2, sticky="w")
                power.grid(row=1, column=1, columnspan=2, sticky="s")

            self.button_references.append(button)
            self.dot_references.append(dot)
            self.power_labels.append(power)
            self.percentage_labels.append(percentage)

    def setup_control_buttons(self):
        # Setup controls for applying percentage
        close_selected_connection = tk.Button(self.top, text="  Close \n  selected  \n  connection  ", fg="black",
                                              bg="#ff432e", width=12, height=3,
                                              command=self.close_selected_connection)
        close_selected_connection.pack(side=tk.RIGHT, padx=(0, 10))
        self.auto_dimming_button = tk.Button(self.top, text="Auto \ncontrol", fg="black", bg="lightblue",
                                             command=self.toggle_auto_control, width=12, height=3)
        self.auto_dimming_button.pack(side=tk.LEFT, pady=10, padx=(10, 0))
        tk.Label(self.top, text="Set the brightness (%):", font="Courier 10").pack(pady=10)
        percentage_entry = tk.Entry(self.top, width=20)
        percentage_entry.pack(pady=10)
        apply_button = tk.Button(self.top, text="Apply",
                                 command=lambda: self.apply_percentage(percentage_entry.get()))
        apply_button.pack(pady=5)
        apply_all_button = tk.Button(self.top, text="Apply for all",
                                     command=lambda: self.apply_percentage_to_all(percentage_entry.get()))
        apply_all_button.pack(pady=5)

    def toggle_auto_control(self):
        # Toggle the state of automatic control, initiating background processing if enabled.
        self.auto_control = not self.auto_control
        if self.auto_control:
            logging.info("Automatic control has been enabled.")
            self.auto_control_counter += 1  # Increment loop counter
            self.auto_dimming_button.config(bg='lightgreen', text="Auto \ncontrol \n(in use)", width=12,
                                            height=3)
            threading.Thread(target=self.auto_control_process, daemon=True).start()
            self.counter_label.config(text=f"Number of automatic executions: {self.auto_control_counter}")
        else:
            logging.info("Automatic control has been disabled.")
            self.auto_dimming_button.config(bg='lightblue', text=f"Auto \ncontrol", width=12, height=3)

    @lru_cache(maxsize=32)
    def fetch_and_parse(self, row_val: int, data_val: int):
        """
        Fetch and parse data from a predefined URL, caching responses.
        used to download limits from external program by API
        Network request and error handling
        """

        url = 'http://yourapiconnection.example'  # use your api data
        auth = ('login', 'password')
        try:
            response = requests.get(url, auth=auth)
            response.raise_for_status()  # This will generate an exception for responses that are not code 2xx
            data = response.json()
            rows = data.get("rows", [])
            return rows[row_val][data_val] if row_val < len(rows) and data_val < len(rows[row_val]) else None
        except requests.RequestException as e:
            messagebox.showerror("Network Error", str(e))
            return None

    @staticmethod
    def send_whatsapp_message(phone, text, api_key):
        # Sends a WhatsApp message using CallMeBot API.
        url = "https://api.callmebot.com/whatsapp.php"
        params = {'phone': phone, 'text': text, 'apikey': api_key}
        session = requests.Session()
        try:
            response = session.get(url, params=params)
            if response.status_code == 200:
                logging.info("Message sent successfully!")
            else:
                logging.error("Failed to send message:", response.status_code, response.text)
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred: {e}")

    @staticmethod
    def interpolate_percentage(par_value, limits, base_percentages):
        # Interpolates the percentage based on the PAR value and the dynamic limits
        if par_value <= limits[0]:
            return 100  # Assuming 100% for values below the first limit
        for i in range(1, len(limits)):
            if limits[i - 1] < par_value <= limits[i]:
                x0, y0 = limits[i - 1], base_percentages[i - 1]
                x1, y1 = limits[i], base_percentages[i]
                return y0 + (par_value - x0) * (y1 - y0) / (x1 - x0)
        return 20  # Assuming 20% for values above the last limit

    def apply_percentage_auto(self, slave_id, percentage):
        # Applies the given percentage of brightness to the specified slave in auto process.
        self.set_slave_address(slave_id)
        self.apply_percentage(int(percentage))

    def auto_control_process(self):
        # Background process for automatic control based on external data.
        slave_row_mappings = {5: 1, 8: 2, 6: 3, 7: 4, 1: 5, 2: 6, 3: 7, 4: 8}
        base_percentages = [100, 80, 60, 40, 20]  # Base interpolate values
        linear_import = self.fetch_and_parse(9, 1)
        linear_export = self.fetch_and_parse(10, 1)
        linear_import_limit = float(self.fetch_and_parse(9, 3).replace(',', '.')) * 1000  # change MW vlaue to kW
        linear_export_limit = float(self.fetch_and_parse(10, 3).replace(',', '.')) * 1000  # change MW vlaue to kW
        while self.auto_control:
            # Check conditions to adjust settings before processing slaves
            reduce_percentage = False
            if linear_import > linear_import_limit - 100 or linear_export > linear_export_limit:
                self.send_whatsapp_message(self.phone, self.text, self.api_key)
                reduce_percentage = True

            #  Fetch data, calculate settings, and apply to slaves
            for slave_id, row_index in slave_row_mappings.items():
                limits = [
                    int(self.fetch_and_parse(row_index, i)) for i in range(2, 7)
                ]
                par_value = int(self.fetch_and_parse(row_index, 1))
                percentage = self.interpolate_percentage(par_value, limits, base_percentages)
                if reduce_percentage:
                    percentage *= 0.9  # reduce percentage by 10% for all slaves

                self.apply_percentage_auto(slave_id, percentage)
                logging.info(f"\n==== Slave: {slave_id}, PAR: {par_value}, percentage: {percentage} ====\n")

            # Increment the counter and update the label after each full iteration of the loop for all slaves
            self.auto_control_counter += 1
            self.top.after(0, lambda: self.counter_label.config(text=f"The number of automatic executions: "
                                                                     f"{self.auto_control_counter}"))
            time.sleep(300)  # Wait 5 min before next iteration

    def run(self):
        # Start the GUI event loop
        self.top.mainloop()


if __name__ == "__main__":
    app = ModbusApp()
    app.run()
