#**************************************************************************
#   IMPORTS
#**************************************************************************

import os
import sys
import math
from math import sqrt
import time
import random
from random import randint

assert sys.version_info[0] == 3, "Code assumes Python 3"

# This mess is because I can't get pygame to install on my mac. Sorry.

NO_PYGAME = 'NO_PYGAME' in os.environ

if not NO_PYGAME:
    import pygame
    from pygame.locals import *
else:
    class Dummy:
        def __call__(self, *args, **kwargs):
            return self
        def __eq__(self, other): return self is other
        def __hash__(self): return hash(None)
        def __init__(self, *args, **kwargs): pass
        def __len__(self): return 0
        def __next__(self): raise StopIteration
        def __repr__(self): return 'Dummy()'

        __exit__ = __init__

        __abs__ = __add__ = __and__ = __call__ = __delattr__ = \
        __delitem__ = __div__ = __enter__ = __floordiv__ = __getattr__ = \
        __getitem__ = __invert__ = __iter__ = __lshift__ = __mod__ = \
        __mul__ = __neg__ = __or__ = __pos__ = __pow__ = __radd__ = \
        __rand__ = __rdiv__ = __reversed__ =  __rfloordiv__ = __rlshift__ = \
        __rmod__ = __rmul__ = __ror__ = __rpow__ = __rrshift__ = __rshift__ = \
        __rsub__ = __rtruediv__ = __rxor__ = __setattr__ = __setitem__ = \
        __sub__ = __truediv__ = __xor__ = \
        __call__

        next = __next__  # Python2

    pygame = Dummy()

#**************************************************************************
#   COLORS
#**************************************************************************

"""
FIREBRICK = (178, 34, 34)
SEASHELL = (255, 245, 238)
ROYAL_BLUE = (65, 105, 225)
WHITE_SMOKE = (245, 245, 245)
WHITE = (255, 255, 255)
PURPLE = (186, 85, 211)
PAPAYA_WHIP = (255, 239, 213)
BISQUE_2 = (238, 213, 183)
BISQUE_3 = (205, 183, 158)
BISQUE_4 = (139, 125, 107)
HONEY_DEW = (131, 139, 131)
"""
BLACK = (0, 0, 0)
DIM_GRAY = (105, 105, 105)
DEEP_RED = (165, 42, 42)
DARK_ORANGE = (255, 140, 0)
LIME_GREEN = (50, 205, 50)

#*************************************************************************
#   SYSTEM SETTINGS
#*************************************************************************

#Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 500
PLAYABLE_SCREEN_WIDTH = SCREEN_WIDTH - 100
PLAYABLE_SCREEN_HEIGHT = SCREEN_HEIGHT - 100

"""
**************************************************************************
    SPRITE GROUPS
**************************************************************************
"""
heroes_list = pygame.sprite.Group()
enemy_list = pygame.sprite.Group()
near_hero_list = pygame.sprite.Group()
all_sprites_list = pygame.sprite.Group()

DEFAULT_SURFACE_SIZE = (30,20)

if NO_PYGAME:
    parent=object
else:
    parent=pygame.sprite.Sprite

class Character(parent):
    """
    Character is the root of the game class tree. A character can be a
    hero or villain. A character is an object that displays and updates
    some kind of sprite on the screen, moves around, performs actions,
    etc.
    """

    def __init__(self, **kwargs):
        """
        Any attributes that are passed in by name will be added to the
        object.
        """
        if not NO_PYGAME:
            super().__init__()

        # Import any attributes specified in the kwargs
        for attr,val in kwargs.items():
            setattr(self, attr, val)

        # Take care of some pygame-specific data
        self.image = pygame.Surface(DEFAULT_SURFACE_SIZE)
        self.rect = self.image.get_rect()
        self.surf = pygame.Surface(DEFAULT_SURFACE_SIZE)

        self.image_dir = os.path.join(*'res/img/chars'.split('/'))

    def get_name(self):
        raise NotImplementedError

    def load_images(self, prefix=None):
        if prefix is None:
            if self.image_prefix is not None:
                prefix = self.image_prefix

        if prefix is None:
            raise ValueError('No image filename prefix given')

        images = {}

        with os.scandir(self.image_path) as diriter:
            for entry in diriter:
                if entry.is_file() and entry.name.startswith(prefix):
                    images[entry.name] = pygame.image.load(entry.path)

        if hasattr(self, images):
            self.images.update(images)
        else:
            self.images = images

"""
**************************************************************************
    CREATING THE HERO CLASS

    Values: NAME, SPEED, LEVEL, HP, STAMINA, FEAR
    Format: player = Hero(str, int, int, int, int, int)

    Example:
    heroBoonrit = Hero("Boonrit", 30, 1, 10000, 50, 20)
**************************************************************************
"""
class Hero(Character):
    def __init__(self, name, level, speed, hp, stamina, fear, blocking, jumping_cooldown, attacking_cooldown, held_cooldown, knockdown_cooldown, stun_cooldown, jumping_timer, attacking_timer, held_timer, knockdown_timer, stun_timer, grabbed_cooldown, grabbed_timer):
        super().__init__()
        self.name = name
        self.speed = speed
        self.level = level
        self.hp = hp
        self.stamina = stamina
        self.fear = fear
        self.blocking = blocking
        self.jumping_cooldown = jumping_cooldown
        self.jumping_timer = jumping_timer
        self.attacking_cooldown = attacking_cooldown
        self.attacking_timer = attacking_timer
        self.held_cooldown = held_cooldown
        self.held_timer = held_timer
        self.knockdown_cooldown = knockdown_cooldown
        self.knockdown_timer = knockdown_timer
        self.stun_cooldown = stun_cooldown
        self.stun_timer = stun_timer

    def jump(self):
        #if self.attacking_cooldown == False and self.held_cooldown == False and self.stun_cooldown == False and self.knockdown_cooldown == False:
        self.jumping_cooldown == True
        ticks = 60

    def held(self, enemy):
        for villan in near_hero_list:
            pass

    def update(self, pressed_keys):

        #if self.held_cooldown:
        for villan in near_hero_list:
            if villan.grabbing_cooldown == True:
                self.held_cooldown == True
                self.rect.x = (villan.rect.x + 30)
                self.rect.y = villan.rect.y
                break

        if self.held_cooldown == True:
            self.held_timer -= 1
            if self.held_timer == 0:
                self.held_cooldown = False
                self.rect.x += 40

        if self.jumping_cooldown == True:
            ticks -= 1

            if ticks == 0:
                self.jumping_cooldown == False
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-3.png'))

            elif ticks <= 30:
                self.rect.y += 3
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-3.png'))
                #self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-jump-down.png'))

            else:
                self.rect.y -= 3
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-3.png'))
                #self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-jump-up.png'))

        if self.attacking_cooldown == True:
            self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-attack-1.png'))
            self.attacking_timer -= 1
            if self.attacking_timer <= 0:
                self.attacking_timer = 0
                self.attacking_cooldown = False
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-3.png'))

        if self.stun_cooldown == True:
            self.stun_timer -= 1
            if self.held_cooldown == True:
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-held-stun.png'))
            elif self.jumping_cooldown == True:
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-jumping-stun.png'))
            elif self.knockdown_cooldown == True:
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-knockdown-stun.png'))
            else:
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-stun.png'))
            if self.stun_timer < 0:
                self.stun_timer = 0
                self.stun_cooldown = False
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-3.png'))

        if self.held_cooldown == True:
            self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-held.png'))
            self.held_timer -= 1
            if self.held_timer <= 0:
                self.held_timer = 0
                self.held_cooldown == False
                self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-3.png'))

        if self.blocking == True:
            self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-block.png'))

        # Jumping
            #self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-jump.png'))

        # If hero isn't blocking, attacking or being stunned, then s(he) is able to move
        if self.blocking == False and self.attacking_cooldown == False and self.stun_cooldown == False and self.held_cooldown == False:
            if pressed_keys[K_LEFT]:
                self.rect.move_ip(-heroBoonrit.speed, 0)

            if pressed_keys[K_RIGHT]:
                self.rect.move_ip(heroBoonrit.speed, 0)

            if pressed_keys[K_UP]:
                self.rect.move_ip(0, -heroBoonrit.speed)

            if pressed_keys[K_DOWN]:
                self.rect.move_ip(0, heroBoonrit.speed)

            if pressed_keys[K_d]:
                self.attacking_cooldown = True
                self.attacking_timer = 20

            if pressed_keys[K_s]:
                self.jumping_cooldown = True
                self.jump()

            if pressed_keys[K_a]:
                self.blocking = True

        # Stop the player from moving too far off the screen

        # Health
        if self.hp <= 0:
            self.kill()
        elif self.hp <= 20:
            #self.image.fill(DEEP_RED)
            self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-1.png'))
        elif self.hp <= 60:
            #self.image.fill(DARK_ORANGE)
            self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-2.png'))
        elif self.hp <= 90:
            #self.image.fill(LIME_GREEN)
            self.image = pygame.image.load(os.path.join('res','img','chars','boonrit-3.png'))
        else:
            pass

# Active character
ac = ["Boonrit", "Hugo", "Joy", "Victoria", "Kelly"]

"""
**************************************************************************
    CREATING THE ENEMY

    Values: COLOR, SPEED, LEVEL, HP, STAMINA, FEAR
    Format: Shit_Clown = Enemy(str, int, int, int, int, int)
    Example:
    Shit_Clown = Enemy("Shit Clown",30,1,10000,50,20)

**************************************************************************
"""

class Enemy(Character):
    def __init__(self, name, level, speed, hp, stamina, fear, blocking_cooldown, jumping_cooldown, punching_cooldown, held_cooldown, knockdown_cooldown, stun_cooldown, jumping_timer, punching_timer, held_timer, knockdown_timer, stun_timer, grabbing_cooldown, grabbing_timer, blocking_timer):
        super().__init__()
        self.image = pygame.image.load(os.path.join('res','img','chars','shit_clown-3.png'))
        #self.image = pygame.Surface([30,20])

        self.name = name
        self.speed = speed
        self.level = level
        self.hp = hp
        self.stamina = stamina
        self.fear = fear
        self.blocking_cooldown = blocking_cooldown
        self.jumping_cooldown = jumping_cooldown
        self.jumping_timer = jumping_timer
        self.punching_cooldown = punching_cooldown
        self.punching_timer = punching_timer
        self.held_cooldown = held_cooldown
        self.held_timer = held_timer
        self.knockdown_cooldown = knockdown_cooldown
        self.knockdown_timer = knockdown_timer
        self.stun_cooldown = stun_cooldown
        self.stun_timer = stun_timer
        self.grabbing_cooldown = grabbing_cooldown
        self.grabbing_timer = grabbing_timer
        self.blocking_timer = blocking_timer

        blocking_cooldown = False
        jumping_cooldown = False
        jumping_coutndown = 0
        attacking_cooldown = False
        attacking_timer = 0
        held_cooldown = False
        held_timer = 0
        knockdown_cooldown = False
        knockdown_timer = 0
        stun_cooldown = False
        stun_timer = 0
        grabbing_cooldown = False
        grabbing_timer = 0
        blocking_timer = 0

    def grab(self, heroBoonrit):
        if self in near_hero_list:
            self.grabbing_cooldown = True
        else:
            self.grabbing_cooldown = False

    def punch(self, heroBoonrit):
        if self in near_hero_list:
            self.punching_cooldown = True
        else:
            return False

    def update(self):
        if self.grabbing_cooldown:
            self.grabbing_timer -= 1
            if self.grabbing_timer == 0:
                self.grabbing_cooldown = False
                self.grabbing_timer = 60

        #if blocking_cooldown == False and held_cooldown == False and knockdown_cooldown == False and stun_cooldown == False and grabbing_cooldown == False:
            # Flip the coin.
            #coin_flip = random.randrange(1,4)
            #if coin_flip == 1:
                #timer -= 1
                #self.rect.move_ip(0, 0)
                #if timer <= 0
        #elif coinFlip == 2:
            #self.rect.move_ip(-1, 0)
        #else:
            #self.rect.move_ip(1, 0)

        #if self.attacking_cooldown == True:
            #self.attacking_timer -= 1
            #if self.attacking_timer <= 0:
                #self.attacking_timer = 0
                #self.attacking_cooldown = False

        if self.hp <= 0:
            self.kill()
        elif self.hp <= 20:
            self.image.fill(DEEP_RED)
        elif self.hp <= 60:
            self.image.fill(DARK_ORANGE)
        elif self.hp <= 90:
            self.image.fill(LIME_GREEN)
        else:
            pass

class Villain(Character):
    def __init__(self):
        cls = type(self)
        attrs = cls.ATTRS if hasattr(cls, 'ATTRS') else {}
        super().__init__(**attrs)
        if not hasattr(self, 'name'):
            _id = self.get_id()
            self.name = self.get_name_fmt().format(_id)

    def __repr__(self):
        cls = type(self).__name__
        return '{}({})'.format(cls, self.__dict__)

    def get_id(self):
        cls = type(self)
        if not hasattr(cls, '_counter'):
            cls._counter = 0

        cls._counter += 1
        return cls._counter

    def get_name_fmt(self):
        cls = type(self)
        if not hasattr(cls, 'NAME_FMT'):
            cls.NAME_FMT = cls.__NAME__ + ' {}'
        return cls.NAME_FMT

class ShitClown(Villain):

    NAME_FMT = 'Shit Clown {}'
    ATTRS = {
        'image_prefix': 'shit_clown',
        'level': 1,
        'speed': 4,
        'hp': 1000,
        'stamina': 10,
        'fear': 90,
    }

if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    sc1 = ShitClown()
    sc2 = ShitClown()
    print(sc1)
    print(sc2)
    exit(0)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
#background_image = 'res' + os.sep + 'images' + os.sep + 'bg-level-1-1-1.jpg'
#pygame.image.load(os.path.join("res","images","bg-level-1-1-1.jpg")).convert()
#bg = pygame.image.load("bg-level-1-1-1.jpg").convert()
#screen.blit(pygame.Surface, [0, 0])

    pygame.init()
    clock = pygame.time.Clock()
    Score = 0

    font_hero_name = pygame.font.SysFont("monospace", 15)

    """
    **************************************************************************
        SPAWNING THE HERO
        Outdate Values: name, speed, level, hp, stamina, fear, blocking, jumping_cooldown, attacking_cooldown, held_cooldown, knockdown_cooldown, jumping_timer, attacking_timer, held_timer, knockdown_timer
    **************************************************************************
    """
# Boonrit, Male, Thailand
    heroBoonrit = Hero("Boonrit",1,3,10000,50,20,False,False,False,False,False,False,False,0,0,0,0,0,0)
#Name
#Level
#Speed
#HP
#Stamina
#Fear
#Blocking
#Jumping Cooldown
#Attacking Cooldown
#Held Cooldown
#Knockdown Cooldown
#Stun Cooldown
#Grabbed Cooldown
#Jumping Countdown
#Attacking Countdown
#Held Countdown
#Knockdown Countdown
#Stun Countdown
#Grabbed Countdown
    heroBoonrit.image = pygame.image.load(os.path.join('res','img','chars','boonrit-3.png')).convert()
    heroBoonrit.rect.x = 100
    heroBoonrit.rect.y = 300
    heroes_list.add(heroBoonrit)
    all_sprites_list.add(heroBoonrit)

    """
    **************************************************************************
        SPAWNING ENEMIES
        Values: name, level, speed, hp, stamina, fear, blocking_cooldown, jumping_cooldown, attacking_cooldown, held_cooldown, knockdown_cooldown, stun_cooldown, jumping_timer, attacking_timer, held_timer, knockdown_timer, stun_timer, grabbing_cooldown, grabbing_timer, blocking_timer
    **************************************************************************
    """

# Spawn 3 Shit Clowns
#def __init__(self, name, level, speed, hp, stamina, fear, blocking_cooldown, jumping_cooldown, attacking_cooldown, held_cooldown, knockdown_cooldown, stun_cooldown, jumping_timer, attacking_timer, held_timer, knockdown_timer, stun_timer, grabbing_cooldown, grabbing_timer, blocking_timer):
    for i in range(2):
        enemyShit_Clown = Enemy("Shit Clown"+str(i), 1, 4, 1000, 10, 90, False, False, False, False, False, False, 0, 0, 0, 0, 0, False, 60, 0)
        enemyShit_Clown.image = pygame.image.load(os.path.join('res','img','chars','shit_clown-3.png')).convert()
        enemyShit_Clown.rect.x = random.randrange(300, 400)
        enemyShit_Clown.rect.y = random.randrange(200, 400)
        enemy_list.add(enemyShit_Clown)
        all_sprites_list.add(enemyShit_Clown)

# Spawn 2 Jack Scrappers
    for i in range(0):
        enemyJack_Scrapper = Enemy("Jack Scrapper "+str(i), 1, 4, 2000, 15, 85, False, False, False, False, False, False, 0, 0, 0, 0, 0, 0, 0)
        enemyJack_Scrapper.image = pygame.image.load(os.path.join('res','img','chars','jack_scrapper-3.png')).convert()
        enemyJack_Scrapper.rect.x = 100 #random.randrange(600, 700)
        enemyJack_Scrapper.rect.y = 100 #random.randrange(200, 400)
        enemy_list.add(enemyJack_Scrapper)
        all_sprites_list.add(enemyJack_Scrapper)

    """
    **************************************************************************
        MAIN GAME LOOP
    **************************************************************************
    """
#screen.blit(heroBoonrit.surf, (30,20))
    contact = pygame.sprite.spritecollide(heroBoonrit, enemy_list, False)


    running = True
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BLACK)
        pygame.draw.rect(screen, DIM_GRAY, (20, 20, 250, 30))
        pygame.draw.rect(screen, DIM_GRAY, (20, 55, 250, 5))
        pygame.draw.rect(screen, DIM_GRAY, (275, 10, 70, 70))

        #pygame.font.Font.render("Boonrit")
        pressed_keys = pygame.key.get_pressed()
        heroBoonrit.update(pressed_keys)
        enemy_list.update()
        near_hero_list.update()

        for villan in enemy_list:
            if (abs(villan.rect.x - heroBoonrit.rect.x)) < 60 and (abs(villan.rect.y - heroBoonrit.rect.y)) < 30:
                near_hero_list.add(villan)
            if (abs(villan.rect.x - heroBoonrit.rect.x)) >= 60 or (abs(villan.rect.y - heroBoonrit.rect.y)) >= 30:
                near_hero_list.remove(villan)
            if villan.grab(heroBoonrit):
                print("Grabbing")

        if heroBoonrit.attacking_cooldown:
            for villan in enemy_list:
                for villan in contact:
                    if villan.blocking_cooldown != True:
                        villan.hp -= 100
                    else:
                        villan.hp -= 10

        #for villan in enemy_list:
            #if (abs(villan.rect.x) - abs(heroBoonrit.rect.x) <= 10) and (abs(villan.rect.y) - abs(heroBoonrit.rect.y) <= 10):
                #near_hero_list.add(villan)
            #if (abs(villan.rect.x) - abs(heroBoonrit.rect.x) > 100) and (abs(villan.rect.y) - abs(heroBoonrit.rect.y) > 10):
                #near_hero_list.remove(villan)
            #if math.sqrt(((villan.rect.x - heroBoonrit.rect.x) **2) + ((villan.rect.x - heroBoonrit.rect.x) **2)) <= 10 and math.sqrt(((villan.rect.y - heroBoonrit.rect.y) **2) + ((villan.rect.y - heroBoonrit.rect.y) **2)) <= 100:
                #near_hero_list.add(villan)
            #if math.sqrt(((villan.rect.x - heroBoonrit.rect.x) **2) + ((villan.rect.x - heroBoonrit.rect.x) **2)) > 10 and math.sqrt(((villan.rect.y - heroBoonrit.rect.y) **2) + ((villan.rect.y - heroBoonrit.rect.y) **2)) > 100:
                #near_hero_list.add(villan)
            #contact = pygame.sprite.spritecollide(heroBoonrit, enemy_list, False)
            #if heroBoonrit.attacking_cooldown:
                #for villan in contact:
                    #if villan.blocking != True:
                        #villan.hp -= 100
                    #else:
                        #villan.hp -= 10


        #screen.blit(bg, (0, 0))
        all_sprites_list.draw(screen)
        pygame.display.flip()
        clock.tick(60)

#*************************************************************************
#   DIAGNOSTICS
#*************************************************************************

        #print(enemy_list)
        #print("Enemy Grabbing: ", enemyShit_Clown.grabbing_cooldown, "| Enemy Countdown", enemyShit_Clown.grabbing_timer )
        #for villan in enemy_list:
        #    print(abs(heroBoonrit.rect.y - villan.rect.y))
        #print(pressed_keys[K_s], heroBoonrit.jumping_cooldown)
        #print("|Boonrit HP| ", heroBoonrit.hp)
        #print(abs(heroBoonrit.rect.y - enemyShit_Clown.rect.y))
        #print("||Shit Clown|| Grabbing = ", enemyShit_Clown.grabbing_cooldown, " Countdown = ", enemyShit_Clown.grabbing_timer, "||Boonrit|| Grabbed = ", heroBoonrit.held_cooldown, " Countdown = ", heroBoonrit.held_timer)
        #print("|Clown HP| ", enemyShit_Clown.hp, "|Boonrit HP| ", heroBoonrit.hp, enemyShit_Clown.grabbing_cooldown, heroBoonrit.held_cooldown)
        #print(" |Score| ", Score)
        #print(" |J| ", heroBoonrit.jumping_cooldown)
        #print(" |A| ", heroBoonrit.attacking_cooldown)
        #print(heroBoonrit.attacking_timer)
        #print(" |H| " , heroBoonrit.held_cooldown)
        #print(" |K| ", heroBoonrit.knockdown_cooldown)
        #print(" |S| ", heroBoonrit.stun_cooldown)
        #print("|Clown HP| ", enemyShit_Clown.hp)
        #print(enemyShit_Clown.image.get_rect())
        #print(enemyShit_Clown.rect)
        #print(heroBoonrit.rect)
        #print(contact)
        #print(enemy_list)
        #print(all_sprites_list)
        #print(heroes_list)
        #for i in enemy_list:
        #    print(i.name, "Grabbing: ", i.grabbing_cooldown)
        #for i in near_hero_list:
        #    print(i.name, "Grabbing: ", i.grabbing_cooldown)
        #for i in enemy_list:
             #print("|Delta X| ", (abs(villan.rect.x) - abs(heroBoonrit.rect.x) <= 100), "|Delta Y| ", (abs(villan.rect.y) - abs(heroBoonrit.rect.y) <= 10))
        #for i in near_hero_list:
            #print(i.name)
        #print(heroBoonrit.image.get_rect())

    pygame.QUIT

    """
        #See if the player has collided with anything
        #enemy_hit_list = pygame.sprite.spritecollide(player, enemy_list, True)
        #for enemy in enemy_hit_list:
        #    player.hp -= 10
        #    print(player.hp)
        #    #Stun the player
        #    player_stun = 3
        #    pygame.mixer.Sound('res\audio\oof.wav').play()
        #    while player_stun > 0:
        #        player_stun -= 1
        #        pygame.time.delay(300)
    """



#******************************************************************************************************
#   NOTES
#******************************************************************************************************
#
#   ISSUE 1:-------------------------------------------------------------------------------------------
#
#
#
#******************************************************************************************************

    """
    **************************************************************************
       CHARACTERS
       Values: name, speed, level, hp, stamina, fear, blocking, jumping_cooldown, attacking_cooldown, held_cooldown, knockdown_cooldown, jumping_timer, attacking_timer, held_timer, knockdown_timer
    **************************************************************************

# Hugo, Male, Brazil
    heroHugo = Hero("Hugo", 30, 1, 10000, 50, 20)
    self.image = pygame.image.load('res\img\chars\hugo-3.png').convert()

# Joy, Female, Trinidad
    heroJoy = Hero("Joy, 30, 1, 10000, 50, 20)
    self.image = pygame.image.load('res\img\chars\joy-3.png').convert()

# Victoria, Female, Ireland
    heroVictoria = Hero("Victoria", 30, 1, 10000, 50, 20)
    self.image = pygame.image.load('res\img\chars\victoria-3.png').convert()

# Kelly, Female, USA
    heroKelly = Hero("Kelly", 30, 1, 10000, 50, 20)
    self.image = pygame.image.load('res\img\chars\kelly-3.png').convert()
    """
