from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput


class CalcApp(App):
    # build: Initializes the application; it will be called only once.
    def build(self):
        self.icon = "app_icon.png"
        # Create App Layout
        body_layout = BoxLayout()
        body_layout.orientation = "vertical"

        self.calc_screen = TextInput()
        self.calc_screen.background_color = "green"
        self.calc_screen.foreground_color = "white"
        self.calc_screen.multiline = False
        self.calc_screen.halign = "right"
        self.calc_screen.font_size = 55
        self.calc_screen.readonly = True
        body_layout.add_widget(self.calc_screen)

        self.operators = ["+", "-", "*", "/"]
        self.last_input_text = ""

        calc_btns = [
            ["7", "8", "9", "/"],
            ["4", "5", "6", "*"],
            ["1", "2", "3", "+"],
            [".", "0", "C", "-"],
            ["="],
        ]
        for row in calc_btns:
            row_layout = BoxLayout()
            for ch in row:
                new_button = Button()
                new_button.text = ch
                new_button.font_size = 30
                new_button.background_color = "yellow"
                new_button.pos_hint = {"center_x": 0.5, "center_y": 0.5}
                row_layout.add_widget(new_button)

                if new_button.text in self.operators:
                    new_button.background_color = "cyan"
                elif new_button.text == "C":
                    new_button.background_color = "red"

                # Add Events to buttons
                if new_button.text == "=":
                    # new_button.on_press = self.handle_equal_press
                    new_button.background_color = "cyan"
                    new_button.font_size = 55
                    new_button.bind(on_press=self.handle_equal_press)
                else:
                    new_button.bind(on_press=self.handle_btn_press)

            body_layout.add_widget(row_layout)

        # return the main layout
        return body_layout

    # Handle events functions
    def handle_btn_press(self, btn_pressed):
        if btn_pressed.text == "C":
            self.calc_screen.text = ""
        elif (self.calc_screen.text == "") and (btn_pressed.text in self.operators):
            return
        elif (btn_pressed.text in self.operators) and (
            self.last_input_text in self.operators
        ):
            return
        else:
            self.calc_screen.text = self.calc_screen.text + btn_pressed.text

        self.last_input_text = btn_pressed.text

    def handle_equal_press(self, btn_pressed):
        if (self.calc_screen.text != "") and (
            self.last_input_text not in self.operators
        ):
            self.calc_screen.text = str(eval(self.calc_screen.text))


if __name__ == "__main__":
    calc_app = CalcApp()
    calc_app.run()
