from tkinter import Tk, LEFT, Frame, Button, Label, Entry, messagebox
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException
from pymodbus.transaction import ModbusSocketFramer

mydata = "192.168.1.100"  # Placeholder for IP address
modbus = 0 # Modbus mode
mflux = 1000 # Maximum light value
slave_address = None  # Initialize as None to handle initial state
total_slaves = 8  # Assuming you have 8 slaves for your setup
button_references = []
slave_names = [
    "place 1", "place 2", "place 3", "place 4",
    "place 5", "place 6", "place 7", "place 8"
]

def set_slave_address(address, button_index):
    """Select a slave address and highlight the corresponding button."""
    global slave_address, button_references
    # Reset color of previously selected button
    if slave_address is not None:
        button_references[slave_address - 1].config(bg='SystemButtonFace')
    # Highlight the newly selected button
    button_references[button_index].config(bg='light green')
    slave_address = address + 1
    print(f"Slave address set to {slave_address}")

def run_sync_simple_client(comm, host, port, my_address, my_slave, my_value):
    """Synchronously run a Modbus client to read/write data."""
    global mflux
    client = ModbusTcpClient(host, port=port, framer=ModbusSocketFramer) if comm == "tcp" else None
    if client is None:
        print(f"Unknown client {comm} selected")
        return

    try:
        if not client.connect():
            print("Connection failed.")
            messagebox.showerror("Connection Error", "Failed to connect to the Modbus server.")
            return
        rr = client.read_holding_registers(address=132, count=1, unit=my_slave)
        if not rr.isError():
            mflux = rr.registers[0]
            print(f"Received data: {rr.registers}")
        else:
            print("Error reading holding registers.")

        client.write_registers(address=my_address, values=[my_value], unit=my_slave)
        print(f"Sent data: {my_value}")
    except ConnectionException as exc:
        print(f"Connection exception encountered: {exc}")
    finally:
        client.close()

def apply_percentage(percentage):
    """Apply a percentage to the current slave's flux value."""
    global slave_address
    if slave_address is None:
        messagebox.showwarning("No Slave Selected", "Please select a slave first.")
        return
    try:
        percentage = int(percentage)
        flux = int(percentage * mflux / 100)
        run_sync_simple_client("tcp", mydata, "502", 38, slave_address, flux)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid integer for percentage.")

def apply_percentage_to_all(percentage):
    """Apply a percentage to all slaves."""
    try:
        percentage = int(percentage)
        flux = int(percentage * mflux / 100)
        for addr in range(1, total_slaves + 1):
            run_sync_simple_client("tcp", mydata, "502", 38, addr, flux)
            print(f"Set {percentage}% to Slave {addr}")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid integer for percentage.")

def on_close():
    """Clean up and close the application."""
    top.destroy()

if __name__ == "__main__":
    top = Tk()
    top.title("ModBus Control")
    top.geometry("420x300")

    Label(top, text="Set Percentage (%):", font="Courier 10").pack(pady=10)
    percentage_entry = Entry(top, width=20)
    percentage_entry.pack(pady=10)
    Button(top, text="Apply", command=lambda: apply_percentage(percentage_entry.get())).pack(pady=10)
    Button(top, text="Apply to All", command=lambda: apply_percentage_to_all(percentage_entry.get())).pack(pady=10)

    # Create slave selection buttons
    frame1 = Frame(top)
    frame1.pack(pady=10)
    frame2 = Frame(top)
    frame2.pack(pady=10)
    for i, name in enumerate(slave_names):
        frame = frame1 if i < 4 else frame2
        button = Button(frame, text=name, command=lambda i=i: set_slave_address(i, i))
        button.pack(side=LEFT, padx=2)
        button_references.append(button)

    top.protocol("WM_DELETE_WINDOW", on_close)
    top.mainloop()