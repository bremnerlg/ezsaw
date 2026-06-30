'''
EZSAW VERSION 3.0.0A
INTRODUCING A GUI FRONTEND 
'''

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder

'''
# Perhaps going to be removed in favour of the more syntactically clear KV lang.
class wizard_intro(AnchorLayout):
    def __init__(self, **kwargs):
        super(wizard_intro, self).__init__(**kwargs)
        self.cols = 2
        self.add_widget(Label(text='Enter a VIN number: '))
        self.vin_entry = TextInput(multiline=False)
        self.add_widget(self.vin_entry)
'''

Builder.load_string('''
<RootWidget>
    GridLayout:
        size_hint: 1, 1
        pos_hint: {'center_x': .5, 'center_y': .5}
        cols:2
        Label:
            text: 'Select vehicle make'
            text_size: self.width-20, self.height-20
            valign: 'center'
        Label:
            text: 'Placeholder (Coming in V1.0.0B)'
            text_size: self.width-20, self.height-20
            valign: 'center'
        Label:
            text: 'Select a vehicle model'
            text_size: self.width-20, self.height-20
            valign: 'center'
        Label:
            text: 'Placeholder (Coming in V1.0.0B)'
            text_size: self.width-20, self.height-20
            valign: 'center'
        Label:
            text: 'Select a vehicle year'
            text_size: self.width-20, self.height-20
            valign: 'center'
        Label:
            text: 'Placeholder (Coming in V1.0.0B)'
            text_size: self.width-20, self.height-20
            valign: 'center'
        Label:
            text: 'or Enter a VIN associated with an EZ product test conducted: '
            text_size: self.width-20, self.height-20
            valign: 'center'
        TextInput:
            focus: True
            text_size: self.width-20, self.height-20

''')


class RootWidget(FloatLayout):
    pass

class ezsaw_proto(App):
    def build(self):
        return RootWidget()

if __name__ == '__main__':
    ezsaw_proto().run()