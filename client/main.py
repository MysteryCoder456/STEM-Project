import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput


class MainGrid(GridLayout):
    def __init__(self, **kwargs):
        super(MainGrid, self).__init__(**kwargs)
        self.cols = 1

        self.add_widget(Label(
            text="STEM App\nThis app will work with the other device to notify you if you left your child in your car."
        ))


class STEMApp(App):
    def build(self):
        return MainGrid()


if __name__ == "__main__":
    STEMApp().run()
