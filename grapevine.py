#!/usr/bin/env python

#**************************************************************************
#   IMPORTS
#**************************************************************************

import os
import os.path
import sys
import math
import time
import random
import weakref

from math import sqrt
from random import randint


assert sys.version_info[0] == 3, "Code assumes Python 3"

try:
    import pygame

    from pygame.locals import *

except ImportError:
    pass

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
DEFAULT_SURFACE_SIZE = (30,20)

#*************************************************************************
#   BASE CLASSES
#*************************************************************************

class PygameResourceManager:
    """One of the frequently mentioned rules for Pygame development is
    "don't load the images more than once!" So this class exists to manage
    the loading of resources - sounds, images, etc.

    The resource manager takes advantage of a concept called a "weak reference"
    which is somewhat advanced. The idea goes like this:

    When you allocate memory in your program to store something, you
    will eventually need to free that memory. If you don't free it, and
    you stop using it, it becomes "lost" - you can't RE-use it, because
    it's still considered in use. This is known as a "memory leak."

    One way to avoid memory leaks is to let the system (Python) manage
    your memory for you. The common way to do that is called "garbage
    collection."

    In a GC system, memory is managed by either explicitly counting 'references'
    to each object (piece of memory), or by looking for things that might
    be a reference to an object. A reference is a pointer. If you say:

        o = [1, 2, 'three']

    You are creating a list (an object) and storing a reference to that
    list in the variable `o`. You are also creating two integer objects,
    and a string object, and storing references to those objects inside
    the list.

    If you then say `o = None`, or just say `del o`, the reference from
    the variable o to the list is broken. At that point, the garbage
    collector can discover that there is a list object that has 0
    references to it.  Great! The collector can free up the memory for
    the list, and remove the references to the other three objects, at
    which point they will have 0 references, and the GC can free up more
    memory!

    The problem with this is that our ResourceManager is going to keep a
    cache of things that have been loaded before. This will be in the form
    of a dictionary of name->value pairs.

    So if there's a great big image sitting in the cache, it will take up
    a bunch of memory. But if there's a reference to it from the cache,
    the garbage collector will never free it up.

    You can see the issue...

    The answer is a "weak reference." This is a special magic thing, that
    has to be supported by the garbage collector, etc. Essentially, its
    a reference that gets treated as a second-class citizen. If the GC
    is looking at an object, and there are no "strong" references, then
    the reference count might as well be 0. Even if there are half a dozen
    weak references to the same object. In that case, <gobble>, the GC
    reclaims the memory.

    So I'm going to use a `weakref.WeakValueDictionary` to store weak
    references to the objects we load. As long as *someone else* is using
    the objects, they'll stay in the cache. But if nobody else gives the
    object any love, then the GC will be free to reclaim the space. It's
    not perfect, but it should get pretty good performance.
    """

    def __init__(self, *, resource_dir='.'):
        self._resources = weakref.WeakValueDictionary()

        if not os.path.isabs(resource_dir):
            dirs = (os.path.dirname(os.path.abspath(__file__)),
                    os.getcwd())

            for base in dirs:
                cand = os.path.normpath(os.path.join(base, resource_dir))
                if os.path.isdir(cand):
                    resource_dir = cand
                    break

            else:
                raise ValueError("Resource dir '{}' is not a directory".format(resource_dir))

        self.resource_dir = resource_dir

    def get_image(self, name):
        if name not in self._resources:
            path = self.get_image_path(name)
            surface = pygame.image.load(path).convert_alpha()
            self._resources[name] = surface
        return self._resources[name]

    def get_image_path(self, name):
        """Overloadable method to compute the path to an image file.
        By overloading this, you can insert subdirs, etc.
        """
        return self.get_path(name)

    def get_music(self, name, *, repeat=None):
        """Note that pygame does not actually load music - it streams
        music. So there is no object in memory. Instead, there is just
        a "current" and a "queue." Instead of storing a resource,
        this just returns True after enqueueing the music.
        """

        path = self.get_music_path(name)
        pygame.mixer.music.queue(path)
        if repeat is not None:
            pygame.mixer.music.play(repeat)

    def get_music_path(self, name):
        """Overloadable method to compute the path to an music file.
        By overloading this, you can insert subdirs, etc.
        """
        return self.get_path(name)

    def get_path(self, *paths):
        return os.path.normpath(os.path.join(self.resource_dir, *paths))

#*************************************************************************
#   Model / View / Controller Base classes
#*************************************************************************

class PygameController:
    """
    I have chosen to adapt a Model/View/Controller approach for this code.
    MVC is a very standard, very popular *design pattern* in widespread use
    today. (So much so, in fact, that it will be hard to get two people to
    agree on the details! But there is plenty of documentation on-line, so
    search away!)

    MVC breaks a system down into three fundamental parts, or types of parts:
    the *model*, the *view* or *views*, and a *controller*.

    ########################################################################

    This class is the base class for Controllers using Pygame. The controller
    is responsible for translating inputs, however they are received, into
    actions and updates in the model and the view. For specific example, a
    joystick is frequently referred to as a "controller." If you play with
    an Xbox or Playstation, the small thing with buttons and joysticks and
    knobs that you hold in your hand is called a "controller."

    A controller will detect that the user is pressing the UP-ARROW, or the
    'W' key, or pushing up on the joystick, or dragging up on a touch screen,
    and translate that into a command to the model that says, "go up." It is
    *not* the job of the controller to know what the limit of going up is, or
    to start drawing sprites, or anything like that. Those are jobs for the
    model (which models the game world) and the view (which deals with the
    display). The controller's job is just to collect inputs, figure out what
    they mean, and tell the rest of the system.

    ########################################################################

    This class knows about all the various Pygame event types, including the
    "special" ones. There is a method, called `event_EVENTTYPE`, for each such
    event type. By default, most of the event types are handled with a simple
    `pass`. Certain types, which should not be received, raise an error instead.
    In order to process a certain type of event, just override the corresponding
    method in your subclass. Don't bother to invoke `super()`, since it will
    either pass or die, and you don't need either one of those behaviors.

    The exception to the above is the event_QUIT handler, which knows that it
    should set `self.active` to False.

    The `run` method is a Pygame event loop. It will loop until the `self.active`
    attribute is false. Each time through the loop it consumes all received
    events, calls the model's `update_frame()` method, waits until enough time
    has passed, checks the `self.active` value, and repeats.
    """

    def __init__(self, *, framerate_hz=16, model=None, support_dropfile=False, view=None):
        """
        The `*,` in the parameter list means that all the following parameters
        are *keyword-only*. This means they can only be specified using the
        `name=value` syntax - it is not possible to just put a value in a
        certain position number.
        """
        self.active = False
        self.framerate_hz = framerate_hz
        self.model = model
        self.view = view

        self.clock = pygame.time.Clock()
        self.support_dropfile = support_dropfile
        self._event_handlers = self._get_event_handlers()

    def event_unsupported(self, evt):
        """Handle any event not defined by Pygame"""
        raise ValueError('Event of unknown type: ' + repr(evt))

    def event_NOEVENT(self, evt):
        """Handle any NOEVENT(0) events. These should never happen by default - creating an event
        of this type is something the user must have done for whatever (bogus) reason."""
        raise ValueError('Events of type NOEVENT should never occur.')

    def event_ACTIVEEVENT(self, evt):
        """Handle ACTIVEEVENT(1): the window has gained focus/become active."""
        pass

    def event_KEYDOWN(self, evt):
        """Handle KEYDOWN(3): A key has been pressed down"""
        pass

    def event_KEYUP(self, evt):
        """Handle KEYUP(3): A key has been released."""
        pass

    def event_MOUSEMOTION(self, evt):
        """Handle MOUSEMOTION(4): A mouse has moved."""
        pass

    def event_MOUSEBUTTONDOWN(self, evt):
        """Handle MOUSEBUTTONDOWN(5): A mouse button has been pressed."""
        pass

    def event_MOUSEBUTTONUP(self, evt):
        """Handle MOUSEBUTTONUP(6): A mouse button has been released."""
        pass

    def event_JOYAXISMOTION(self, evt):
        """Handle JOYAXISMOTION(7): A joystick has moved on at least one axis."""
        pass

    def event_JOYBALLMOTION(self, evt):
        """Handle JOYBALLMOTION(8): Joyball/trackball has been moved."""
        pass

    def event_JOYHATMOTION(self, evt):
        """Handle JOYHATMOTION(9): Joyhat switch has been pressed."""
        pass

    def event_JOYBUTTONDOWN(self, evt):
        """Handle JOYBUTTONDOWN(10): Joystick button pressed."""
        pass

    def event_JOYBUTTONUP(self, evt):
        """Handle JOYBUTTONUP(11): Joystick button released."""
        pass

    def event_QUIT(self, evt):
        """Handle QUIT(12): User clicks the close-window button, or whatever."""
        self.active = False

    def event_SYSWMEVENT(self, evt):
        """Handle SYSWMEVENT(13): System-specific/Window-Manager specific event."""
        pass

    def event_VIDEORESIZE(self, evt):
        """Handle VIDEORESIZE(16): The video window has been resized"""
        pass

    def event_VIDEOEXPOSE(self, evt):
        """Handle VIDEOEXPOSE(17): Certain portions of the window must be redrawn."""
        pass

    def event_USEREVENT_0(self, evt):
        """Handle USEREVENT+0(24): Custom user event."""
        pass

    def event_USEREVENT_1(self, evt):
        """Handle USEREVENT+1(25): Custom user event."""
        pass

    def event_USEREVENT_2(self, evt):
        """Handle USEREVENT+2(26): Custom user event."""
        pass

    def event_USEREVENT_3(self, evt):
        """Handle USEREVENT+3(27): Custom user event."""
        pass

    def event_USEREVENT_4(self, evt):
        """Handle USEREVENT+4(28): Custom user event."""
        pass

    def event_USEREVENT_5(self, evt):
        """Handle USEREVENT+5(29): Custom user event."""
        pass

    def event_USEREVENT_6(self, evt):
        """Handle USEREVENT+6(30): Custom user event."""
        pass

    def event_USEREVENT_7(self, evt):
        """Handle USEREVENT+7(31): Custom user event."""
        pass

    def event_USEREVENT_DROPFILE(self, evt):
        """Handle USEREVENT_DROPFILE(4096): the user has drag-and-dropped a file into the
        window."""
        pass

    def _get_event_handlers(self):
        """Return an object that can be indexed by event type to access the event handler
        methods. The result of obj[evt_type] will be a bound method on self that can be
        called. If self.support_dropfile is true (not the default) a dictionary is used.
        This will show slightly worse performance. In the default case (support_dropfile is
        False) a tuple is used.
        """
        _event_handlers = (
            self.event_NOEVENT,       self.event_ACTIVEEVENT,     self.event_KEYDOWN,
            self.event_KEYUP,         self.event_MOUSEMOTION,     self.event_MOUSEBUTTONDOWN,
            self.event_MOUSEBUTTONUP, self.event_JOYAXISMOTION,   self.event_JOYBALLMOTION,
            self.event_JOYHATMOTION,  self.event_JOYBUTTONDOWN,   self.event_JOYBUTTONUP,
            self.event_QUIT,          self.event_SYSWMEVENT,      self.event_unsupported,
            self.event_unsupported,   self.event_VIDEORESIZE,     self.event_VIDEOEXPOSE,
            self.event_unsupported,   self.event_unsupported,     self.event_unsupported,
            self.event_unsupported,   self.event_unsupported,     self.event_unsupported,
            self.event_USEREVENT_0,   self.event_USEREVENT_1,     self.event_USEREVENT_2,
            self.event_USEREVENT_3,   self.event_USEREVENT_4,     self.event_USEREVENT_5,
            self.event_USEREVENT_6,   self.event_USEREVENT_7,

        )

        if self.support_dropfile:
            handlers = {et:eh for et, eh in enumerate(_event_handlers)}
            handlers[pygame.USEREVENT_DROPFILE] = self.event_USEREVENT_DROPFILE,
        else:
            handlers = _event_handlers

        return handlers

    def run(self):
        """
        Run the main event loop, accepting events from the OS, dispatching them to the
        various handlers. Continue running until `self.active` is falsy. Each time
        through the loop, call the model's `update_frame` method to notify it that
        time has passed.
        """
        handlers = self._event_handlers

        # Cache these function lookups.
        clock_tick = self.clock.tick
        model_update_frame = self.model.update_frame
        pygame_event_get = pygame.event.get

        self.active = True

        # An event handler will clear self.active to quit. Always
        # reload!
        while self.active:
            for event in pygame_event_get():
                handlers[event.type](event)

            # Call this once per frame.
            model_update_frame()
            # Model or user could change framerate. Always reload it!
            clock_tick(self.framerate_hz)
            self.view.update()

        self.model.quit()

class PygameModel:
    """
    I have chosen to adapt a Model/View/Controller approach for this code.
    MVC is a very standard, very popular *design pattern* in widespread use
    today. (So much so, in fact, that it will be hard to get two people to
    agree on the details! But there is plenty of documentation on-line, so
    search away!)

    MVC breaks a system down into three fundamental parts, or types of parts:
    the *model*, the *view* or *views*, and a *controller*.

    ########################################################################

    This class is the base class for Models using Pygame. The model is the
    "world." It is responsible for *modelling* all the parts of the system,
    deciding what the behaviors are, what happens, who lives or dies, etc.

    If the game starts with a hero fighting an orc, the model is responsible
    for keeping track of the positions of the hero and the orc, how many hit
    points each one has, which direction they are moving, etc. If the hero
    drinks a healing potion, the model is responsible for removing the potion
    from inventory, increasing the hit points, and telling the *View* that
    there should be a glow around the hero for a second or two.

    ########################################################################

    This class knows about the methods that are called by the PygameController
    class. Each of them is minimally implemented. The constructor saves whatever
    arguments are passed in.
    """

    def __init__(self, *, view=None):
        """
        The `*,` in the parameter list means that all the following parameters
        are *keyword-only*. This means they can only be specified using the
        `name=value` syntax - it is not possible to just put a value in a
        certain position number.
        """
        self.view = view

    def quit(self):
        """Call to notify the model that the controller is exiting its run-loop. This is a
        program-is-ending signal, not game-is-over.
        """
        pass

    def update_frame(self):
        """Call once per frame (16-60 times per second) to notify the model of the passage
        of time in-game.
        """
        pass

class PygameView:
    """
    I have chosen to adapt a Model/View/Controller approach for this code.
    MVC is a very standard, very popular *design pattern* in widespread use
    today. (So much so, in fact, that it will be hard to get two people to
    agree on the details! But there is plenty of documentation on-line, so
    search away!)

    MVC breaks a system down into three fundamental parts, or types of parts:
    the *model*, the *view* or *views*, and a *controller*.

    ########################################################################

    This class is the base class for Views using Pygame. The View is the game's
    display. It is responsible for providing a visual interface that the user
    can read in order to react to what is happening in-game.

    If the game is going to be implemented in a windowing system with 2d graphics
    and sound, it is the View's responsibility to create the window, render the
    graphics, and play the sounds. If the game is going to be played on a terminal
    with 80x25 character display and just the occasional "beep", it is the View's
    responsibility to initialize curses (or whatever terminal package) and send
    escape codes to move the X's and O's around on-screen.

    ########################################################################

    This class doesn't know much, just yet.
    """

    def __init__(self, *, resolution=None, resource_manager=None):
        """
        Create a View object for Pygame. This will handle collecting and
        dispatching events, creating and updating a graphics window, and
        maintaining the correct frame rate.

        The `*,` in the parameter list means that all the following parameters
        are *keyword-only*. This means they can only be specified using the
        `name=value` syntax - it is not possible to just put a value in a
        certain position number.
        """

        self.resolution = resolution
        self.resource_manager = resource_manager

        pygame.init()

        self.screen = pygame.display.set_mode(resolution)
        self.background = None

        self.set_background(self.screen)

        # Check if pygame.font is available. This actually depends on
        # libsdl_ttf, I think, and so it's possible for pygame to init
        # without font support. Record the results.
        try:
            pygame.font.init()
            self.pygame_has_font = True
        except NotImplementedError:
            self.pygame_has_font = False

    def set_background(self, bg):
        if self.background != bg:
            self.background = bg
            self.screen.blit(bg, (0,0))

    def update(self):
        pygame.display.update()

#*************************************************************************
#   CLASSES
#*************************************************************************

class GrapevineController(PygameController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class GrapevineResourceManager(PygameResourceManager):
    def get_image_path(self, name):
        return self.get_path('img', name)

    def get_music_path(self, name):
        return self.get_path('music', name)

class GrapevineView(PygameView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pygame.display.set_caption("Grapevine")

        bg = self.resource_manager.get_image('background-1.png')
        self.set_background(bg)
        #background_image = 'res' + os.sep + 'images' + os.sep + 'bg-level-1-1-1.jpg'
        #pygame.image.load(os.path.join("res","images","bg-level-1-1-1.jpg")).convert()
        #bg = pygame.image.load("bg-level-1-1-1.jpg").convert()
        #screen.blit(pygame.Surface, [0, 0])
        #font_hero_name = pygame.font.SysFont("monospace", 15)
        pygame.display.flip()


class Character(pygame.sprite.Sprite):
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

    def update(self, *args):
        raise NotImplementedError

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
        #for villan in near_hero_list:
        pass

    def update(self, pressed_keys):

        #if self.held_cooldown:
        #for villan in near_hero_list:
        #    if villan.grabbing_cooldown == True:
        #        self.held_cooldown == True
        #        self.rect.x = (villan.rect.x + 30)
        #        self.rect.y = villan.rect.y
        #        break

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

    def grab(self, heroBoonrit):
        #if self in near_hero_list:
        #    self.grabbing_cooldown = True
        #else:
        #    self.grabbing_cooldown = False
        pass

    def punch(self, heroBoonrit):
        #if self in near_hero_list:
            #self.punching_cooldown = True
        #else:
            #return False
        pass

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
        """
        Keep an integer counter in the class object of each subclass.
        Look for the `_counter` attribute, create it to 0 if not found.
        Each time get_id is called, it increments the _counter and
        returns that value. Thus, each subclass gets a stream of ids
        like 1, 2, 3, ...
        """
        cls = type(self)
        if not hasattr(cls, '_counter'):
            cls._counter = 0

        cls._counter += 1
        return cls._counter

    def get_name_fmt(self):
        """
        Return the name format string for a subclass. If there is no
        NAME_FMT attribute on the subclass, just use the subclass's name
        as the basis for the format. This will be formatted with a number
        from get_id to produce an instance's name, like 'Shit Clown 1'.
        """
        cls = type(self)
        if not hasattr(cls, 'NAME_FMT'):
            cls.NAME_FMT = cls.__NAME__ + ' {}'
        return cls.NAME_FMT

class JackScrapper(Villain):
    NAME_FMT = 'Jack Scrapper {}'
    ATTRS = {
        'image_prefix': 'jack_scrapper',
        'level': 1,
        'speed': 4,
        'hp': 2000,
        'stamina': 15,
        'fear': 85,
    }

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

class GrapevineGame(PygameModel):
    def __init__(self, view=None):
        super().__init__()
        self.view = view

def parse_cli():
    """Parse command-line switches, provide defaults, and return them in a nice dictionary.
    """

    args = {}
    args['resolution'] = (SCREEN_WIDTH, SCREEN_HEIGHT)
    args['framerate'] = 30
    return args

def main():
    args = parse_cli()

    rmgr = GrapevineResourceManager(resource_dir='res')
    view = GrapevineView(resolution=args['resolution'],
            resource_manager=rmgr)
    model = GrapevineGame(view=view)
    controller = PygameController(model=model, view=view, framerate_hz=args['framerate'])
    controller.run()

    sys.exit(0)

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


if __name__ == '__main__':
    if not pygame.image.get_extended():
        print("Pygame not built with extended image format support. Sorry.")
        exit(1)

    main()

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
