import pyglet
from pyglet.window import mouse, key # Importado 'key' para o atalho de tela cheia
import os
import webbrowser
import random
import main

class Menu:
    def __init__(self):

        self.window = pyglet.window.Window(
            width=800, height=600, 
            caption='Minecraft Clone - Menu',
            resizable=True
        )
        self.window.set_mouse_visible(True)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Carregando o Background
        try:
            self.background = pyglet.image.load(os.path.join(script_dir, 'op_1.jpg'))
        except Exception as e:
            print(f"Erro ao carregar op_1.jpg: {e}")
            self.background = None

        # Carregando som de clique
        try:
            self.click_sound = pyglet.media.load(os.path.join(script_dir, 'click1.ogg'), streaming=False)
        except Exception as e:
            print(f"Erro ao carregar click1.ogg: {e}")
            self.click_sound = None

        self.batch = pyglet.graphics.Batch()
        
        # Inicialização dos Labels (posições serão atualizadas no on_resize)
        self.title_label = pyglet.text.Label('MINECRAFT CLONE',
                                  font_name='Arial', font_size=48, bold=True,
                                  anchor_x='center', batch=self.batch)

        self.subtitle_messages = [
            "Brutal não sobrou nada pro beta",
            "não pesqusise oque e sonichu!",
            "^W^",
            "Minerar nunca foi tão divertido!"
        ]
        self.current_subtitle = 0
        
        self.subtitle_label = pyglet.text.Label(self.subtitle_messages[self.current_subtitle],
                                  font_name='Arial', font_size=18,
                                  anchor_x='center', batch=self.batch)
        
        self.start_label = pyglet.text.Label('JOGAR',
                                  font_name='Arial', font_size=28,
                                  anchor_x='center', batch=self.batch)
        
        self.credits_label = pyglet.text.Label('CRÉDITOS',
                                  font_name='Arial', font_size=28,
                                  anchor_x='center', batch=self.batch)
        
        self.exit_label = pyglet.text.Label('SAIR',
                                  font_name='Arial', font_size=28,
                                  anchor_x='center', batch=self.batch)

        self.credits_batch = pyglet.graphics.Batch()
        
        self.credits_title = pyglet.text.Label('CRÉDITOS',
                                  font_name='Arial', font_size=36, bold=True,
                                  anchor_x='center', batch=self.credits_batch)
        
        self.credits_text = pyglet.text.Label('Desenvolvido por: HAM\n\nTecnologias utilizadas:\n- Pyglet\n- Python',
                                  font_name='Arial', font_size=16, multiline=True,
                                  width=600, align='center',
                                  anchor_x='center', anchor_y='center', batch=self.credits_batch)
        
        self.github_button = pyglet.text.Label('GitHub do Projeto',
                                  font_name='Arial', font_size=22,
                                  anchor_x='center', color=(100, 149, 237, 255),
                                  batch=self.credits_batch)
        
        self.docs_button = pyglet.text.Label('Documentação',
                                  font_name='Arial', font_size=22,
                                  anchor_x='center', color=(100, 149, 237, 255),
                                  batch=self.credits_batch)
        
        self.back_button = pyglet.text.Label('VOLTAR',
                                  font_name='Arial', font_size=24,
                                  anchor_x='center', batch=self.credits_batch)

        self.show_credits = False
        pyglet.clock.schedule_interval(self.change_subtitle, 5.0)
        
        # Registro de eventos atualizado
        self.window.push_handlers(
            self.on_draw, 
            self.on_mouse_press,
            self.on_mouse_motion,
            self.on_resize,    # Novo evento
            self.on_key_press  # Novo evento para F11
        )

    # --- NOVAS FUNÇÕES ---

    def on_resize(self, width, height):
        """Repocisiona os elementos quando a janela muda de tamanho"""
        cx, cy = width // 2, height // 2

        # Menu Principal
        self.title_label.x, self.title_label.y = cx, height - 100
        self.subtitle_label.x, self.subtitle_label.y = cx, height - 150
        self.start_label.x, self.start_label.y = cx, cy + 50
        self.credits_label.x, self.credits_label.y = cx, cy - 20
        self.exit_label.x, self.exit_label.y = cx, cy - 90

        # Créditos
        self.credits_title.x, self.credits_title.y = cx, height - 100
        self.credits_text.x, self.credits_text.y = cx, cy + 100
        self.github_button.x, self.github_button.y = cx, cy - 50
        self.docs_button.x, self.docs_button.y = cx, cy - 100
        self.back_button.x, self.back_button.y = cx, cy - 180

    def on_key_press(self, symbol, modifiers):
        """Atalho para Tela Cheia"""
        if symbol == key.F11:
            self.window.set_fullscreen(not self.window.fullscreen)

    # --- FIM DAS NOVAS FUNÇÕES ---

    def change_subtitle(self, dt):
        self.current_subtitle = (self.current_subtitle + 1) % len(self.subtitle_messages)
        self.subtitle_label.text = self.subtitle_messages[self.current_subtitle]

    def play_click_sound(self):
        if self.click_sound:
            self.click_sound.play()

    def open_web_page(self, url):
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"Erro ao abrir URL: {e}")

    def on_draw(self):
        self.window.clear()
        if self.background:
            self.background.blit(0, 0, width=self.window.width, height=self.window.height)
        
        if self.show_credits:
            self.credits_batch.draw()
        else:
            self.batch.draw()

    def update_button_hover(self, label, x, y):
        """Lógica de hover simplificada para funcionar em qualquer resolução"""
        # Verifica se o mouse está dentro de uma área aproximada ao redor do texto
        width_half = 100 
        height_half = 20
        if (label.x - width_half < x < label.x + width_half and 
            label.y < y < label.y + height_half * 2):
            label.color = (255, 215, 0, 255)
            return True
        else:
            if label in [self.github_button, self.docs_button]:
                label.color = (100, 149, 237, 255)
            else:
                label.color = (255, 255, 255, 255)
            return False

    def on_mouse_motion(self, x, y, dx, dy):
        if not self.show_credits:
            self.update_button_hover(self.start_label, x, y)
            self.update_button_hover(self.credits_label, x, y)
            self.update_button_hover(self.exit_label, x, y)
        else:
            self.update_button_hover(self.github_button, x, y)
            self.update_button_hover(self.docs_button, x, y)
            self.update_button_hover(self.back_button, x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == mouse.LEFT:
            self.play_click_sound()
            
            if not self.show_credits:
                if self.update_button_hover(self.start_label, x, y):
                    self.window.close()
                    main.main()
                elif self.update_button_hover(self.credits_label, x, y):
                    self.show_credits = True
                elif self.update_button_hover(self.exit_label, x, y):
                    pyglet.app.exit()
            else:
                if self.update_button_hover(self.github_button, x, y):
                    self.open_web_page("https://github.com/seu-usuario/minecraft-clone")
                elif self.update_button_hover(self.docs_button, x, y):
                    self.open_web_page("https://pyglet.readthedocs.io/")
                elif self.update_button_hover(self.back_button, x, y):
                    self.show_credits = False

    def run(self):
        pyglet.app.run()

if __name__ == '__main__':
    menu = Menu()
    menu.run()