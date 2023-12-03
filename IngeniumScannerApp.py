from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
import camera4kivy

class Layout(App):
    def build(self):
        layout = BoxLayout(padding=100)

        btn = Button(text="QR-Scanner", background_color=[0, 0, 1, 1])
        btn.bind(on_press=Camera(play=True, index=1, resolution=(640, 480)))

        layout.add_widget(btn)
        return layout

    #def openscanner(self, instance):
     #   return Camera(play=True, index=1, resolution=(640, 480))


if __name__ == "__main__":
    app = Layout()
    app.run()
