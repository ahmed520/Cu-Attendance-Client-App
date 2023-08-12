from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import RoundedRectangle, Color
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import socket
import time
import threading

connected = False
s = None

Builder.load_string("""
<RoundedButton>:
    canvas.before:
        Color:
            rgba: self.background_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [0]
""")

class RoundedButton(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        self.background_color = (0.117, 0.564, 1, 0.5)
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (dp(120), dp(50))
        self.padding = (dp(10), dp(5))
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.disabled = True

    def update_rect(self, *args):
        pass

class MyApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        logo = Image(source='logo.png', size_hint=(1, None), height=dp(200))
        layout.add_widget(logo)

        label = Label(text='Attendance', font_size=dp(40), color=(1, 1, 1, 1))
        layout.add_widget(label)

        self.output_textbox = Label(markup=True, text='', color=(0, 0, 1, 1))
        scroll_view = ScrollView(do_scroll_x=False)
        scroll_view.add_widget(self.output_textbox)
        layout.add_widget(scroll_view)  # Add the output text widget and scroll view here

        self.update_output_textbox("Output text will appear here.")  # Initial message

        self.username_input = TextInput(hint_text='Username', multiline=False, size_hint_y=None, height=dp(60),
                                   foreground_color=(1, 1, 1, 1), background_color=(1, 1, 1, 0.1))
        layout.add_widget(self.username_input)

        self.password_input = TextInput(hint_text='Password', password=True, multiline=False, size_hint_y=None, height=dp(60),
                                   foreground_color=(1, 1, 1, 1), background_color=(1, 1, 1, 0.1))
        layout.add_widget(self.password_input)
        self.server_ip = ""
        self.connect_button = RoundedButton()
        self.connect_button.add_widget(Label(text='Send', size_hint=(1, None), height=dp(40), halign='center', valign='middle'))
        self.connect_button.bind(on_press=self.send_credentials)
        exit_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        exit_layout.add_widget(self.connect_button)
        exit_layout.add_widget(Label())
        self.status_label = Label(text='Not connected', color=(1, 0, 0, 1))
        exit_layout.add_widget(self.status_label)
        layout.add_widget(exit_layout)

        Clock.schedule_once(self.connect_on_startup, 5)
        return layout
    
    def update_output_textbox(self, text):
        # Use the + operator instead of the append method to concatenate the new text to the existing text
        #new_text = self.output_textbox.text + f"[color=0000FF]{text}[/color]\n"
        new_text = f"[color=0000FF]{text}[/color]\n"
        # Check if the new text is different from the current text before updating
        if new_text != self.output_textbox.text:
            # Schedule update_output_textbox with Clock
            Clock.schedule_once(lambda dt: setattr(self.output_textbox, "text", new_text))


    def connect_on_startup(self, dt):
        self.update_output_textbox("Attempting to connect to server...")
        Clock.schedule_once(self.start_listen_broadcast, 0.1)  # Start listening in the next frame
        

    def start_listen_broadcast(self, dt):
        self.bcast_thread = threading.Thread(target=self.listen_broadcast)
        self.bcast_thread.start()
    def start_recieve_thread(self, dt):
        self.recieve_thread = threading.Thread(target=self.receive_message)
        self.recieve_thread.start()


    def receive_message(self):
        global connected,s
        while True:
            # If the client is connected to the server, try to receive data from it
            if connected:
                try:
                    data = s.recv(1024)
                    if not data:
                        Clock.schedule_once(lambda dt: self.update_output_textbox("Server closed the connection"))
                        self.update_status_label(connected)
                        break
                    Clock.schedule_once(lambda dt: self.update_output_textbox(data.decode()))
                except ConnectionResetError:
                    # If connection reset, print an error message and set the connected flag to False
                    Clock.schedule_once(lambda dt: self.update_output_textbox("Error: Connection to server lost."))
                    connected = False
                    self.update_status_label(connected)
                    s.close()
                    
    def send_message(self, instance):
        global connected, s
        username = self.username_input.text
        password = self.password_input.text
        
        # Check if either username or password is empty
        if not username or not password:
            self.show_popup("Please fill in both username and password first.")
            return
        
        message = f'{username}:{password}'
        
        if connected:
            try:
                s.send(message.encode())
                self.update_output_textbox(f"Sent: {message}")
            except Exception as e:
                self.update_output_textbox(f"Error sending message: {str(e)}")
        else:
            self.show_popup("Not connected to server. Cannot send message.")
    
    def show_popup(self, message):
        popup = Popup(title='Alert', content=Label(text=message), size_hint=(None, None), size=(dp(500), dp(150)))
        popup.open()
        
                    
    def listen_broadcast(self):
        global connected
        while True:
            if not connected:
                # Schedule update_output_textbox with Clock
                Clock.schedule_once(lambda dt: self.update_output_textbox("Listening for broadcasts..."))
                # Create a UDP socket
                bcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Bind the socket to the port 5005
                bcast_sock.bind(("", 5005))
                # Loop until a valid broadcast message is received
                while True:
                    try:
                        # Receive data and address from the socket
                        data, addr = bcast_sock.recvfrom(1024)
                        if data:
                            # Decode the data as UTF-8
                            data = data.decode()
                            # Check if the data starts with the expected prefix
                            if data.startswith('I am the server my IP is :'):
                                # Extract the server IP address from the data
                                self.server_ip = data.split(':')[1]
                                # Schedule update_output_textbox with Clock
                                Clock.schedule_once(lambda dt: self.update_output_textbox(data))
                                connected = True
                                # Break out of the loop
                                break
                    except socket.error as e:
                        # Ignore socket errors and continue listening
                        continue
                    except KeyboardInterrupt:
                        # Handle keyboard interrupt and exit the loop
                        break
                # Close the socket
                bcast_sock.close()
                #connect_to_server()
                Clock.schedule_once(self.connect_to_server, 5)
                self.update_output_textbox(f"{self.server_ip}:{port}")

    def connect_server(self, server_ip):
        global s
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((server_ip, port))
            self.update_output_textbox(f"Connected to server at {server_ip}:{port}")
            return True
        except ConnectionRefusedError:
            self.update_output_textbox("Connection refused. Retrying...")
            return False

    def update_status_label(self, connected):
        if connected:
            # Schedule update_output_textbox with Clock
            Clock.schedule_once(self.update_output_textbox_connected)
            # Schedule update_status_label with Clock
            Clock.schedule_once(self.update_status_label_connected)
        else:
            # Schedule update_output_textbox with Clock
            Clock.schedule_once(self.update_output_textbox_not_connected)
            # Schedule update_status_label with Clock
            Clock.schedule_once(self.update_status_label_not_connected)

    # Define the functions that will be scheduled by Clock
    def update_output_textbox_connected(self, dt):
        #self.update_output_textbox("Connected to server.")
        print("hi")

    def update_status_label_connected(self, dt):
        self.status_label.text = 'Connected'
        self.status_label.color = (0, 1, 0, 1)
        self.connect_button.disabled = False
        self.connect_button.background_color = (0.117, 0.564, 1, 1)
        

    def update_output_textbox_not_connected(self, dt):
        #self.update_output_textbox("Not connected to server.")
        print("hi")
    def update_status_label_not_connected(self, dt):
        self.status_label.text = 'Not connected'
        self.status_label.color = (1, 0, 0, 1)
        self.connect_button.disabled = True
        self.connect_button.background_color = (0.117, 0.564, 1, 0.5)


    def connect_to_server(self, dt=None):
        global connected
        self.update_output_textbox("Attempting to connect to server...")
        
        # Check if the server_ip value is available in self.server_ip
        if self.server_ip:
            server_ip = self.server_ip
            # Update the status label based on whether we were able to connect to the server
            connected = self.connect_server(server_ip)
            self.update_status_label(connected)
            Clock.schedule_once(self.start_recieve_thread, 0.2)
            if not connected:
                self.update_output_textbox("Failed to connect to server. Retrying...")
                # Schedule the connect_to_server function again after 5 seconds
                # Use a unique event name to avoid scheduling multiple times
                Clock.schedule_once(self.connect_to_server, 5, "connect_event")
        else:
            # If the server_ip value is not available yet, schedule the connect_to_server function again after 1 second
            # Use a unique event name to avoid scheduling multiple times
            Clock.schedule_once(self.connect_to_server, 1, "connect_event")


    def send_credentials(self, instance):
        self.update_output_textbox("Exiting the application...")
        popup = Popup(title='Confirm Send', content=BoxLayout(orientation='vertical', spacing=dp(10)), size_hint=(None, None), size=(dp(500), dp(150)))
        popup.content.add_widget(Label(text='Are you sure you entered the right credentials?'))
        button_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
        def confirm_send(instance):
            self.send_message(instance)  # Call the send_message function
            popup.dismiss()  # Close the popup
            
        yes_button = Button(text='Yes', background_color=(1, 0.149, 0, 1), size_hint=(None, None), size=(dp(100), dp(50)))
        yes_button.bind(on_press=confirm_send)
        
        no_button = Button(text='No', background_color=(0.117, 0.564, 1, 1), size_hint=(None, None), size=(dp(100), dp(50)))
        no_button.bind(on_press=popup.dismiss)
        
        button_layout.add_widget(yes_button)
        button_layout.add_widget(no_button)
        popup.content.add_widget(button_layout)
        popup.open()

if __name__ == '__main__':
    port = 12345
    MyApp().run()
