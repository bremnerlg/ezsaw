'''
EZSAW VERSION 3.0.0A
INTRODUCING A GUI FRONTEND 
'''

import kivy
kivy.require('2.3.1')
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class wizard_intro(GridLayout):
    def __init__(self, **kwargs):
        super(wizard_intro, self).__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text='Enter a VIN number: '))
        self.vin_entry = TextInput(multiline=False)
        self.add_widget(self.vin_entry)

class ezsaw_proto(App):
    def build(self):
        return wizard_intro()

if __name__ == '__main__':
    ezsaw_proto().run()