import pygame
import math
import sys

# Domyślne ustawienia
digits = 6
time_steps = 10 ** (digits - 1)
WIDTH, HEIGHT = 1280, 720


class Block:
    def __init__(self, x, m, v, offset, block_img, screen_height):
        self.initial_x = x
        self.initial_v = v
        self.x = x
        self.v = v
        self.m = m
        self.offset = offset
        self.width = block_img.get_width()
        self.img = block_img
        self.y = screen_height - block_img.get_height() - 100

    def update(self):
        self.x += self.v

    def show(self, surface):
        surface.blit(self.img, (int(self.x), self.y))

    def hit_wall(self):
        return self.x <= 150

    def reverse(self):
        self.v *= -1

    def collide(self, other):
        return self.x + self.width > other.x

    def bounce(self, other):
        total_mass = self.m + other.m
        new_v = ((self.m - other.m) * self.v + 2 * other.m * other.v) / total_mass
        return new_v

    def reset(self):
        self.x = self.initial_x
        self.v = self.initial_v


class Button:
    def __init__(self, rect, text, font, bg_color=(180, 180, 180, 0), text_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.original_bg_color = bg_color
        self.text_color = text_color
        self.clicked_state = False
        self.click_animation_time = 0
        self.is_hovered = False
        self.hover_color = (
            min(255, self.bg_color[0] + 30),
            min(255, self.bg_color[1] + 30),
            min(255, self.bg_color[2] + 30),
            150  # Przezroczystość dla hover
        )

    def draw(self, surface):
        # Tworzymy powierzchnię dla przycisku z przezroczystością
        button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)

        # Kolor tła z przezroczystością
        if self.clicked_state:
            self.click_animation_time -= 1
            if self.click_animation_time <= 0:
                self.clicked_state = False
            current_color = (*self.original_bg_color[:3], 100)  # Ciemniejszy przy kliknięciu
        elif self.is_hovered:
            current_color = self.hover_color
        else:
            current_color = self.bg_color

        # Rysujemy tło przycisku
        pygame.draw.rect(button_surface, current_color, (0, 0, self.rect.width, self.rect.height), border_radius=8)

        # Białe obramowanie
        pygame.draw.rect(button_surface, (255, 255, 255, 200), (0, 0, self.rect.width, self.rect.height), 2,
                         border_radius=8)

        # Tekst
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        button_surface.blit(text_surf, text_rect)

        # Rysujemy cały przycisk na głównej powierzchni
        surface.blit(button_surface, self.rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def trigger_click_animation(self):
        self.clicked_state = True
        self.click_animation_time = 10


class SimulationUI:
    def __init__(self, digits, width, height):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Collision Simulation")
        self.clock = pygame.time.Clock()
        self.running = True

        self.digits = digits
        self.min_digits = 1
        self.max_digits = 9
        self.width = width
        self.height = height
        self.count = 0

        self.update_time_steps()

        # Ładowanie zasobów
        self.block_img1 = pygame.image.load('data/block.png').convert_alpha()
        self.block_img2 = pygame.image.load('data/img.png').convert_alpha()
        self.background_img = pygame.image.load('data/background.png').convert()
        self.background_img = pygame.transform.scale(self.background_img, (width, height))
        self.overlay_img = pygame.image.load('data/overlay.png').convert_alpha()
        self.overlay_img = pygame.transform.scale(self.overlay_img, (width, height))
        self.clack_sound = pygame.mixer.Sound('data/clack.wav')
        self.big_font = pygame.font.SysFont(None, 72)
        self.button_font = pygame.font.SysFont(None, 40)
        self.label_font = pygame.font.SysFont(None, 30)

        # Bloki
        self.block1 = Block(300, 1, 0, 0, self.block_img1, self.height)
        self.block2 = Block(800, math.pow(100, self.digits - 1), -4 / self.time_steps, 20, self.block_img2, self.height)

        self.simulation_active = False

        # Przyciski
        button_width = 120
        button_height = 50
        button_y = 43
        button_x = 970

        # Kolory przycisków z przezroczystością
        start_color = (35, 198, 139, 150)  # Ostatnia wartość to alpha (przezroczystość)
        reset_color = (234, 58, 75, 150)
        inc_dec_color = (153, 153, 153, 150)

        self.start_button = Button((button_x, button_y, button_width, button_height),
                                   "Start", self.button_font, bg_color=start_color)
        self.reset_button = Button((button_x + button_width + 10, button_y, button_width, button_height),
                                   "Reset", self.button_font, bg_color=reset_color)

        # Przyciski do zmiany liczby cyfr
        increase_x = 700
        self.decrease_button = Button((increase_x, button_y + 25, 80, 30), "-", self.button_font,
                                      bg_color=inc_dec_color)
        self.increase_button = Button((increase_x + 90, button_y + 25, 80, 30), "+", self.button_font,
                                      bg_color=inc_dec_color)

    def update_time_steps(self):
        self.time_steps = 10 ** (self.digits - 1)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for button in [self.start_button, self.reset_button, self.decrease_button, self.increase_button]:
            button.is_hovered = button.rect.collidepoint(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.start_button.is_clicked(event.pos):
                    self.start_button.trigger_click_animation()
                    self.simulation_active = True
                elif self.reset_button.is_clicked(event.pos):
                    self.reset_button.trigger_click_animation()
                    self.reset_simulation()
                elif self.decrease_button.is_clicked(event.pos):
                    self.decrease_button.trigger_click_animation()
                    self.change_digits(-1)
                elif self.increase_button.is_clicked(event.pos):
                    self.increase_button.trigger_click_animation()
                    self.change_digits(1)

    def change_digits(self, change):
        new_digits = self.digits + change
        if self.min_digits <= new_digits <= self.max_digits:
            self.digits = new_digits
            self.update_time_steps()
            self.reset_simulation()
            self.block2 = Block(800, math.pow(100, self.digits - 1), -4 / self.time_steps, 20,
                                self.block_img2, self.height)

    def simulate_collisions(self):
        if not self.simulation_active:
            return

        clack_happened = False
        for _ in range(self.time_steps):
            if self.block1.collide(self.block2):
                v1 = self.block1.bounce(self.block2)
                v2 = self.block2.bounce(self.block1)
                self.block1.v = v1
                self.block2.v = v2
                clack_happened = True
                self.count += 1

            if self.block1.hit_wall():
                self.block1.reverse()
                clack_happened = True
                self.count += 1

            self.block1.update()
            self.block2.update()

        if clack_happened:
            self.clack_sound.play()

    def reset_simulation(self):
        self.count = 0
        self.simulation_active = False
        self.block1.reset()
        self.block2.reset()

    def render(self):
        # Najpierw tło
        self.screen.blit(self.background_img, (0, 0))

        # Bloki
        self.block1.show(self.screen)
        self.block2.show(self.screen)

        # Licznik zderzeń
        count_text = self.big_font.render(str(self.count).zfill(self.digits), True, (255, 255, 255))
        self.screen.blit(count_text, (self.width // 2 + 200, 115))

        # Wyświetlanie liczby cyfr π
        digits_text = self.big_font.render(str(self.digits), True, (255, 255, 255))
        self.screen.blit(digits_text, (self.width // 2 + 262, 47))

        # Przyciski
        self.start_button.draw(self.screen)
        self.reset_button.draw(self.screen)
        self.decrease_button.draw(self.screen)
        self.increase_button.draw(self.screen)

        # Nakładka na wierzchu wszystkiego
        self.screen.blit(self.overlay_img, (0, 0))

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.simulate_collisions()
            self.render()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    simulation = SimulationUI(digits, WIDTH, HEIGHT)
    simulation.run()