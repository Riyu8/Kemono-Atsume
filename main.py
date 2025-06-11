import pygame
import sys
import os

# 日本語フォント初期化
try:
    jp_font = pygame.font.Font("assets/NotoSansJP-VariableFont_wght.ttf", 36)
    jp_font_large = pygame.font.Font("assets/NotoSansJP-VariableFont_wght.ttf", 48)
    jp_font_small = pygame.font.Font("assets/NotoSansJP-VariableFont_wght.ttf", 24)
except Exception as e:
    print(f"フォント読み込みエラー: {e}")
    jp_font = pygame.font.SysFont(None, 36)
    jp_font_large = pygame.font.SysFont(None, 48)
    jp_font_small = pygame.font.SysFont(None, 24)
import glob
import math
import asyncio
import random

class GameState:
    def __init__(self):
        self.current_screen = "title"
        self.selected_animal_index = 0
        self.selected_item = None
        self.collected_animals = []
        self.all_base_collected = False
        self.animals = []
        self.hidden_animals = []

class AssetLoader:
    @staticmethod
    def load_image(path, target_size=None):
        try:
            base_name = os.path.splitext(path)[0]
            files = glob.glob(f"./{base_name}*.png") + glob.glob(f"./{base_name}*.PNG")  # Web用相対パス指定追加
            if not files:
                raise FileNotFoundError(f"ファイルが見つかりません: {path}")
            
            original_image = pygame.image.load(files[0]).convert_alpha()
            
            if target_size:
                width, height = original_image.get_size()
                ratio = min(target_size[0]/width, target_size[1]/height)
                new_size = (int(width*ratio), int(height*ratio))
                
                resized_image = pygame.Surface(target_size, pygame.SRCALPHA)
                scaled = pygame.transform.smoothscale(original_image, new_size)
                
                x = (target_size[0] - new_size[0]) // 2
                y = (target_size[1] - new_size[1]) // 2
                resized_image.blit(scaled, (x, y))
                return resized_image
            return original_image
        except Exception as e:
            print(f"警告: 画像の読み込みに失敗しました ({path}): {str(e)}")
            placeholder = pygame.Surface(target_size or (50, 50), pygame.SRCALPHA)
            color = (255, 0, 0) if not target_size or target_size[0] > 100 else (0, 255, 0)
            if target_size:
                pygame.draw.rect(placeholder, color, (0, 0, target_size[0], target_size[1]))
            else:
                pygame.draw.rect(placeholder, color, (0, 0, 50, 50))
            return placeholder

    @staticmethod
    def load_sound(path):
        try:
            sound = pygame.mixer.Sound(path)
            print(f"サウンド読み込み成功: {path}")
            return sound
        except Exception as e:
            print(f"警告: サウンドの読み込みに失敗しました ({path}): {str(e)}")
            return None

class Item:
    def __init__(self, name, item_type, image_path, power=1):
        self.name = name
        self.type = item_type
        self.power = power
        self.image = AssetLoader.load_image(image_path, (50, 50))
        self.rect = pygame.Rect(0, 0, 50, 50)

    def draw(self, screen, pos):
        self.rect.topleft = pos
        screen.blit(self.image, self.rect)

class Animal:
    def __init__(self, name, favorite_food, favorite_toy, base_image, evolved_image):
        self.name = name
        self.favorite_food = favorite_food
        self.favorite_toy = favorite_toy
        self.affection = 0
        self.collected = False
        self.is_evolved = False
        self.is_animating = False
        self.animation_frame = 0
        self.animation_duration = 30  # 0.5秒間（60fps想定）
        
        # 画像のパスを保存
        self.base_image_path = base_image
        self.evolved_image_path = evolved_image
        
        # 画像の読み込み
        self.base_image = AssetLoader.load_image(base_image, (300, 300))
        # 進化画像が辞書型の場合は初期化時には読み込まない
        if isinstance(evolved_image, dict):
            self.evolved_image = None
        else:
            self.evolved_image = AssetLoader.load_image(evolved_image, (300, 300))
        self.image = self.base_image
        self.rect = self.image.get_rect(center=(400, 300))
        
    def evolve(self):
        """ケモノを進化させる"""
        self.is_evolved = True
        
        # 進化画像が辞書型の場合の処理
        if isinstance(self.evolved_image_path, dict):
            # 使用回数に基づいて進化形態を決定
            # 進化条件を閾値5回に修正
            if self.fire_count >= 5 and self.sun_count >= 5 and self.fire_count == self.sun_count:
                image_path = self.evolved_image_path["true"]
                print("≪真の不死鳥が目覚めた！≫")
            elif self.fire_count >= 5 and self.fire_count > self.sun_count:
                image_path = self.evolved_image_path["flame"]
            elif self.sun_count >= 5 and self.sun_count > self.fire_count:
                image_path = self.evolved_image_path["sun"]
            else:
                # 閾値に達していない場合はベース画像を維持
                image_path = self.base_image_path
            
            # 進化画像を読み込み
            try:
                self.evolved_image = AssetLoader.load_image(image_path, (300, 300))
            except Exception as e:
                print(f"進化画像の読み込みに失敗しました: {str(e)}")
                self.evolved_image = self.base_image
                
        self.image = self.evolved_image if self.evolved_image else self.base_image
        self.is_animating = True
        self.animation_frame = 0
        print(f"{self.name}が進化しました！")
        print(f"新しい姿: {image_path if isinstance(self.evolved_image_path, dict) else self.evolved_image_path}")

        # 進化エフェクト用のパーティクル（画面サイズに合わせて調整）
        self.effect_particles = [
            (random.randint(50, 750), random.randint(50, 550))  # 画面端を避ける
            for _ in range(50)
        ]
        
    def increase_affection(self, amount):
        """親密度を増加させ、進化条件をチェック"""
        self.affection = min(100, self.affection + amount)
        if self.affection >= 50 and not self.collected:
            self.collected = True
            
        # 全ケモノ共通の進化条件
        if not self.is_evolved and self.affection >= 100:
            self.evolve()
        
        # アニメーション開始
        self.is_animating = True
        self.animation_frame = 0

    def update(self):
        """アニメーションの状態を更新"""
        if self.is_animating:
            self.animation_frame += 1
            if self.animation_frame >= self.animation_duration:
                self.is_animating = False
                self.animation_frame = 0
        
    def draw(self, screen):
        # 進化エフェクト
        if hasattr(self, 'effect_particles') and self.is_evolved:
            for i, (x, y) in enumerate(self.effect_particles):
                try:
                    alpha = 255 * (1 - i/len(self.effect_particles))
                    color = (255, 215, 0, int(alpha))
                    pygame.draw.circle(screen, color, (x, y), 3)
                except Exception as e:
                    print(f"パーティクル描画エラー: {str(e)}")
                
        if self.is_animating:
            # 進化中のアニメーション
            if self.is_evolved:
                # フェードイン効果
                alpha = min(255, self.animation_frame * 15)
                temp_surface = pygame.Surface((self.image.get_width(), self.image.get_height()), pygame.SRCALPHA)
                temp_surface.blit(self.image, (0, 0))
                temp_surface.set_alpha(alpha)
                screen.blit(temp_surface, self.rect)
            else:
                # 通常の跳ねるアニメーション
                scale = 1.0 + 0.1 * math.sin(math.pi * self.animation_frame / self.animation_duration)
                offset_y = -10 * math.sin(math.pi * self.animation_frame / self.animation_duration)
                
                scaled_image = pygame.transform.smoothscale(self.image, 
                    (int(self.rect.width * scale), int(self.rect.height * scale)))
                new_rect = scaled_image.get_rect(center=(self.rect.centerx, self.rect.centery + offset_y))
                screen.blit(scaled_image, new_rect)
        else:
            screen.blit(self.image, self.rect)

        # 進化メッセージ
        if self.is_evolved and self.animation_frame < 30:
            text = jp_font_large.render(f"{self.name} evolved!", True, (255, 215, 0))
            text_rect = text.get_rect(center=(400, 500))
            screen.blit(text, text_rect)
        
        # ハートマークを確実に表示するためテキストで表示
        heart_text = f"♥ {self.affection}/100"  # Unicodeハート記号を使用
        text = jp_font.render(heart_text, True, (255, 0, 0))
        text_rect = text.get_rect(center=(400, 100))
        screen.blit(text, text_rect)

class TitleScreen:
    def __init__(self):
        self.title_font = None
        self.start_button = pygame.Rect(300, 400, 200, 50)
        
    def load_assets(self):
        try:
            self.title_font = jp_font_large
        except:
            try:
                self.title_font = pygame.font.SysFont("sans-serif", 48)  # 代替フォント1
            except:
                self.title_font = pygame.font.SysFont(None, 48)  # 最終的な代替
    
    def draw(self, screen):
        try:
            bg_image = AssetLoader.load_image("assets/kemono_star_screen.png", (800, 600))
            screen.blit(bg_image, (0, 0))
        except:
            screen.fill((135, 206, 235))
        
        pygame.draw.rect(screen, (50, 150, 50), self.start_button, border_radius=10)
        try:
            button_font = jp_font_small
            start_text = button_font.render("START GAME", True, (255, 255, 255))
            screen.blit(start_text, (400 - start_text.get_width()//2, 415))
        except:
            try:
                button_font = pygame.font.SysFont("sans-serif", 28)  # 代替フォント1
                start_text = button_font.render("ゲームスタート", True, (255, 255, 255))
                screen.blit(start_text, (400 - start_text.get_width()//2, 415))
            except:
                button_font = pygame.font.SysFont(None, 28)  # 最終的な代替
                start_text = button_font.render("ゲームスタート", True, (255, 255, 255))
                screen.blit(start_text, (400 - start_text.get_width()//2, 415))
    
    def handle_event(self, event, game_state):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button.collidepoint(event.pos):
                game_state.current_screen = "main"
                return True
        return False

class CollectionScreen:
    def __init__(self, animals):
        self.visible = False
        self.animals = animals
        self.current_page = 0
        self.items_per_page = 8
        
    def draw(self, screen):
        if not self.visible:
            return
            
        overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        
        pygame.draw.rect(screen, (255, 255, 255), (50, 50, 700, 500), border_radius=10)
        
        try:
            title = jp_font_large.render("Kemono Collection", True, (0, 0, 0))
            screen.blit(title, (400 - title.get_width()//2, 70))
        except Exception as e:
            print(f"フォント描画エラー: {e}")
            font = pygame.font.SysFont(None, 40)
            title = font.render("あなたのケモノコレクション", True, (0, 0, 0))
            screen.blit(title, (400 - title.get_width()//2, 70))
        
        total_pages = (len(self.animals) + self.items_per_page - 1) // self.items_per_page
        start_index = self.current_page * self.items_per_page
        end_index = min(start_index + self.items_per_page, len(self.animals))
        
        start_x = 100
        start_y = 120
        for i in range(start_index, end_index):
            animal = self.animals[i]
            idx = i - start_index
            row = idx // 4
            col = idx % 4
            x = start_x + col * 150
            y = start_y + row * 180
            
            # ベース画像のパスを使用
            thumbnail = AssetLoader.load_image(animal.base_image_path, (120, 120))
            screen.blit(thumbnail, (x, y))
            
            try:
                name_text = jp_font_small.render(animal.name, True, (0, 0, 0))
                screen.blit(name_text, (x + 60 - name_text.get_width()//2, y + 130))
            except Exception as e:
                print(f"フォント描画エラー: {e}")
                font = pygame.font.SysFont(None, 14)
                name_text = font.render(animal.name, True, (0, 0, 0))
                screen.blit(name_text, (x + 60 - name_text.get_width()//2, y + 130))
        
        if total_pages > 1:
            try:
                font = jp_font_small
                if self.current_page > 0:
                    pygame.draw.rect(screen, (100, 100, 100), (300, 480, 50, 30), border_radius=5)
                    prev_text = font.render("<", True, (255, 255, 255))
                    screen.blit(prev_text, (325 - prev_text.get_width()//2, 485))
                
                page_text = font.render(f"{self.current_page+1}/{total_pages}", True, (0, 0, 0))
                screen.blit(page_text, (400 - page_text.get_width()//2, 485))
                
                if self.current_page < total_pages - 1:
                    pygame.draw.rect(screen, (100, 100, 100), (450, 480, 50, 30), border_radius=5)
                    next_text = font.render(">", True, (255, 255, 255))
                    screen.blit(next_text, (475 - next_text.get_width()//2, 485))
            except:
                try:
                    font = pygame.font.SysFont("sans-serif", 28)  # 代替フォント1
                    if self.current_page > 0:
                        pygame.draw.rect(screen, (100, 100, 100), (300, 480, 50, 30), border_radius=5)
                        prev_text = font.render("前", True, (255, 255, 255))
                        screen.blit(prev_text, (325 - prev_text.get_width()//2, 485))
                    
                    page_text = font.render(f"{self.current_page+1}/{total_pages}", True, (0, 0, 0))
                    screen.blit(page_text, (400 - page_text.get_width()//2, 485))
                    
                    if self.current_page < total_pages - 1:
                        pygame.draw.rect(screen, (100, 100, 100), (450, 480, 50, 30), border_radius=5)
                        next_text = font.render("次", True, (255, 255, 255))
                        screen.blit(next_text, (475 - next_text.get_width()//2, 485))
                except:
                    font = pygame.font.SysFont(None, 28)  # 最終的な代替
                    if self.current_page > 0:
                        pygame.draw.rect(screen, (100, 100, 100), (300, 480, 50, 30), border_radius=5)
                        prev_text = font.render("前", True, (255, 255, 255))
                        screen.blit(prev_text, (325 - prev_text.get_width()//2, 485))
                    
                    page_text = font.render(f"{self.current_page+1}/{total_pages}", True, (0, 0, 0))
                    screen.blit(page_text, (400 - page_text.get_width()//2, 485))
                    
                    if self.current_page < total_pages - 1:
                        pygame.draw.rect(screen, (100, 100, 100), (450, 480, 50, 30), border_radius=5)
                        next_text = font.render("次", True, (255, 255, 255))
                        screen.blit(next_text, (475 - next_text.get_width()//2, 485))
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                self.visible = not self.visible
                return True
            elif event.key == pygame.K_RIGHT:
                total_pages = (len(self.animals) + self.items_per_page - 1) // self.items_per_page
                if self.current_page < total_pages - 1:
                    self.current_page += 1
                    return True
            elif event.key == pygame.K_LEFT:
                if self.current_page > 0:
                    self.current_page -= 1
                    return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN and self.visible:
            if 300 <= event.pos[0] <= 350 and 480 <= event.pos[1] <= 510 and self.current_page > 0:
                self.current_page -= 1
                return True
            elif 450 <= event.pos[0] <= 500 and 480 <= event.pos[1] <= 510 and self.current_page < (len(self.animals) + self.items_per_page - 1) // self.items_per_page - 1:
                self.current_page += 1
                return True
                
        return False

async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    print("Pygame初期化完了")  # デバッグ用出力
    pygame.display.set_caption("Kemono Collection")
    clock = pygame.time.Clock()
    
    game_state = GameState()
    
    pygame.mixer.init()
    
    try:
        bgm_path = "assets/bgm_main.ogg"
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.set_volume(0.2)  # 音量を20%に設定
        pygame.mixer.music.play(-1)
        print(f"BGM再生: {bgm_path} (音量: 0.2)")
    except Exception as e:
        print(f"警告: BGMの読み込みに失敗しました: {str(e)}")
    
    sounds = {
        "food": AssetLoader.load_sound("assets/food.wav"),
        "toy": AssetLoader.load_sound("assets/toy.wav"),
        "happy": AssetLoader.load_sound("assets/happy.wav"),
        "switch": AssetLoader.load_sound("assets/switch.wav")
    }
    
    items = [
        Item("Fish", "food", "assets/fish.png", 5),
        Item("Meat", "food", "assets/meat.png", 5),
        Item("Carrot", "food", "assets/carrot.png", 5),
        Item("Ball", "toy", "assets/ball.png", 5),
        Item("Bone", "toy", "assets/bone.png", 5),
        Item("Sword", "toy", "assets/sword.png", 5),
        Item("Rainbow", "food", "assets/rainbow.png", 5),
        Item("Fire", "food", "assets/flame.png", 5),
        Item("Star", "toy", "assets/star.png", 5),
        Item("Sun", "toy", "assets/sun.png", 5)
    ]
    
    base_animal_data = [
        {
            "name": "Cat",
            "food": "Fish",
            "toy": "Ball",
            "base_image": "assets/cat_2.png",
            "evolved_image": "assets/universe.PNG"
        },
        {
            "name": "Rabbit",
            "food": "Carrot",
            "toy": "Carrot",
            "base_image": "assets/rabbit_2.png",
            "evolved_image": "assets/king.png"  # ウサギ進化後
        },
        {
            "name": "Dog",
            "food": "Meat",
            "toy": "Bone",
            "base_image": "assets/dog_2.png",
            "evolved_image": "assets/streetStyle.png"  # イヌ進化後
        },
        {
            "name": "Fox",
            "food": "Grape",
            "toy": "Ball",
            "base_image": "assets/fox_2.png",
            "evolved_image": "assets/casualStyle.png"  # 進化後画像を更新
        },
        {
            "name": "Tiger",
            "food": "Meat",
            "toy": "Ball",
            "base_image": "assets/tiger_2.png",
            "evolved_image": "assets/steamPunk.png"
        },
        {
            "name": "Dragon",
            "food": "Gem",
            "toy": "Sword",
            "base_image": "assets/dragon_2.png",
            "evolved_image": "assets/Medievalfantasystyle.png"
        },
        {
            "name": "Wolf",
            "food": "Meat",
            "toy": "Bone",
            "base_image": "assets/wolf_2.png",
            "evolved_image": "assets/wizard.png"  # ウィザードオオカミに変更
        }
    ]
    
    hidden_animals_data = [
        {
            "name": "Unicorn",
            "food": "Rainbow",
            "toy": "Star",
            "base_image": "assets/unicorn_2.png",
            "evolved_image": "assets/mage.png"
        },
        {
            "name": "Phoenix",
            "food": "Fire",
            "toy": "Sun",
            "base_image": "assets/phoenix_2.png",
            "evolved_image": "assets/afterPhoenix.png"
        }
    ]
    
    for data in base_animal_data:
        animal = Animal(
            name=data["name"],
            favorite_food=data["food"],
            favorite_toy=data["toy"],
            base_image=data["base_image"],
            evolved_image=data["evolved_image"]
        )
        game_state.animals.append(animal)
    
    for data in hidden_animals_data:
        animal = Animal(
            name=data["name"],
            favorite_food=data["food"],
            favorite_toy=data["toy"],
            base_image=data["base_image"],
            evolved_image=data["evolved_image"]
        )
        game_state.hidden_animals.append(animal)
    
    title_screen = TitleScreen()
    title_screen.load_assets()
    collection_screen = CollectionScreen(game_state.animals)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if game_state.current_screen == "title":
                if title_screen.handle_event(event, game_state):
                    continue
            
            elif game_state.current_screen == "main":
                if collection_screen.handle_event(event):
                    continue
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, item in enumerate(items):
                        if item.rect.collidepoint(event.pos):
                            game_state.selected_item = item
                            print(f"{item.name}を選択しました")
                            break
                    else:
                        if event.button == 1:
                            if game_state.selected_item:
                                animal = game_state.animals[game_state.selected_animal_index]
                                item = game_state.selected_item
                                
                                is_favorite = False
                                if (item.type == "food" and item.name == animal.favorite_food) or \
                                   (item.type == "toy" and item.name == animal.favorite_toy):
                                    is_favorite = True
                                
                                if is_favorite:
                                    # 好物アイテム使用時の処理（不要なカウント処理を削除）
                                    animal.increase_affection(item.power)
                                    if sounds["happy"]:
                                        sounds["happy"].play()
                                else:
                                    if item.type == "food" and sounds["food"]:
                                        sounds["food"].play()
                                    elif item.type == "toy" and sounds["toy"]:
                                        sounds["toy"].play()
                                
                                if not game_state.all_base_collected:
                                    base_collected = all(a.collected for a in game_state.animals[:len(base_animal_data)])
                                    if base_collected and game_state.hidden_animals:
                                        game_state.animals.extend(game_state.hidden_animals)
                                        game_state.all_base_collected = True
                                        print("隠しケモノが解放されました！")
                                        if sounds["happy"]:
                                            sounds["happy"].play()
                                
                        elif event.button == 3:
                            game_state.selected_animal_index = (game_state.selected_animal_index + 1) % len(game_state.animals)
                            print(f"ケモノを切り替え: {game_state.animals[game_state.selected_animal_index].name}")
                            if sounds["switch"]:
                                sounds["switch"].play()
        
        screen.fill((255, 255, 255))
        
        if game_state.current_screen == "title":
            title_screen.draw(screen)
        
        elif game_state.current_screen == "main":
            current_animal = game_state.animals[game_state.selected_animal_index]
            current_animal.update()
            current_animal.draw(screen)
            
            for i, item in enumerate(items):
                item.draw(screen, (50 + i * 60, 500))
            
            if game_state.selected_item:
                pygame.draw.rect(screen, (0, 255, 0), game_state.selected_item.rect, 3)
            
            collection_screen.draw(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)  # 非同期処理のために必要

    pygame.mixer.music.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
