import pygame
import math


# This is a game called (rather unoriginally) Jumpbot, in which you play a robot
# that jumps around on platforms, collecting coins, avoiding monsters, and opening
# portals. Instructions on how to play the game are given inside the game.
# The game sometimes tends to get slow / drop frames. Unfortunately, I have not had
# the time to optimize for the amount of operations happening each frame. It is
# something I might do down the line, but I wanted to hand in this assignment before
# the exam for the Advanced Course.
# I put more time into this project than I initially anticipated. It became quite
# large. I haven't 'cleaned up' some parts of the code, so please forgive any
# unused variables that are declared or any comments that refer to functions or
# methods that no longer exist. :)


class Robot:
    def __init__(self, window: pygame.surface.Surface):
        self.__robot = pygame.image.load("robot.png")
        # Setting window and determining window sizes
        self.__window = window
        self.__window_height = window.get_height()
        self.__window_width = window.get_width()
        # Setting initial coordinates and separately storing the initial y value
        self.__x = 0
        self.__y_initial = 579
        # self.__y = self.__y_initial
        self.__y = self.__y_initial
        self.__x_previous = self.__x
        self.__y_previous = self.__y
        # Setting hights for jumps and double jumps separately. Generally, having the
        # double jump value a little higher 'feels' better in this 'game'.
        self.__height_of_jump = 13
        self.__height_of_double_jump = 18
        self.__double_jump_is_active = False
        # Setting initial velocities in both planes, and also the previous velocity in the
        # horizontal plane (for the deceleration method)
        self.__previous_x_velocity = 0
        self.__x_velocity = 0
        self.__y_velocity = self.__height_of_jump
        # Gravity value
        self.__gravity = 1
        # Variable to check whether the robot is falling, becomes True when there is
        # no platform directly below the robot while the robot isn't jumping
        self.__falling = False
        # Variable containing the number of frames in which the robot cant be
        # controlled. Standard value is 0.
        self.__x_bump = 0
        self.__x_bump_max = 15  # Standard maximum value
        # Variable that is True when the robot has just spawned
        self.__spawning = True
        self.__spawn_counter_max = 15  # Number of frames the spawning status lasts
        self.__spawn_counter = self.__spawn_counter_max

    def play(self, inputs: dict, platform_data: list):
        # Main method of the robot. Calls on the self.__move() method which
        # calculates new coordinates and changes input values when necessary
        # Ignore inputs (i.e. don't __move()) when spawning until counter runs out
        if self.__spawning:
            if self.__spawn_counter == 0:
                self.__spawning = False
                self.__spawn_counter = self.__spawn_counter_max
            else:
                self.__spawn_counter -= 1
        else:
            self.__move(inputs, platform_data)
        # Draw the robot on the screen on the updated coordinates
        self.__window.blit(self.__robot, (self.__x, self.__y))

    def __move(self, inputs: dict, platform_data: list):
        # After bumping horizontally into a platform, the player loses
        # control of the robot in the horizontal plane for a brief moment.
        # This creates sense of recoil after bumping into a wall.
        # We don't want to change the inputs dictionary directly, as we
        # want to be able to keep the left or right key pressed and
        # keep bumping into the wall that way. We create a 'copy' of the
        # dictionary with the "to_left" and "to_right" keys set to False
        # while the x-bump frames are > 0. When the frames have run out,
        # the original dictionary will be put into self.__total_x_velocity(),
        # so no new key press is needed to move in a given direction.
        if self.__x_bump > 0:
            self.__x_velocity = self.__total_x_velocity(
                {
                    "to_left": False,
                    "to_right": False,
                    "is_running": inputs["is_running"],
                    "is_jumping": inputs["is_jumping"],
                }
            )
            # Decrease the remaining bump animation frames by 1
            self.__x_bump -= 1
        else:
            # Normal situation (where the robot isn't inside the
            # frames after a wall bump)
            self.__x_velocity = self.__total_x_velocity(inputs)

        # Increase the x coordinate by the horizontal velocity
        self.__x += self.__x_velocity

        # Fall detection, checks if robot is in the air or walking on a platform
        # Lower robot position by 1 pixel and check if clipping on the bottom takes place
        if not inputs["is_jumping"] and not self.__falling:
            self.__y += 1
            hit_offsets_for_fall_detection = self.__collision(platform_data)
            # If the bottom offset is not equal to 1, this means the robot is not standing
            # on a platform, but in fact in the air/falling
            if abs(hit_offsets_for_fall_detection["bottom"]) != 1:
                # Falling is set to True
                self.__falling = True
                # Velocity is set to 0 instead of jump height
                self.__y_velocity = 0
            else:
                # If the robot is on a platform, the velocity stays equal to jump height
                self.__y_velocity = self.__height_of_jump
            # Decrease y position by 1 pixel again to return to pre-check position
            self.__y -= 1

        if inputs["is_jumping"] or self.__falling:
            # Can use the double jump after falling off a ledge as well
            if inputs["is_double_jumping"] and not self.__double_jump_is_active:
                self.__double_jump_is_active = True
                self.__y_velocity = self.__height_of_double_jump
            # Decrease y-coordinate by the velocity. Pre-jump on a platform velocity is positive,
            # (equal to 'jump height' variable), meaning the robot will go up the number of pixels
            # in 'jump height' in 1 frame. If no hit is detected after changing the y-coordinate
            # (checked by if and elif statements below), then the y-velocity for the next frame
            # is decreased by the gravity value (standard -1), meaning the robot will move up 1
            # less pixel in the next frame, and will eventually come down.
            # When a hit is detected with the head of the robot against a higher platform, the robot
            # falls down directly (velocity is set to 0 right away and becomes negative in the next
            # frame). When a hit is detected with the feet of the robot (i.e. landing), velocity is
            # set to jump height and jumping inputs are set to False (so the player can jump again).
            # self.__falling is also set to False after landing.
            self.__y -= self.__y_velocity
            # Obtain collision offsets
            hit_offsets = self.__collision(platform_data)
            # Situation when hitting a platform with the robot's top, i.e. from below.
            if (
                hit_offsets["top"] != 0
                and self.__y_velocity >= 0
                and (not self.__y_previous < self.__y + hit_offsets["top"])
            ):
                self.__y += hit_offsets["top"]
                self.__y_velocity = 0
            # Situation when hitting a platform with the robot's bottom, i.e. from above / landing.
            elif (
                hit_offsets["bottom"] != 0
                and self.__y_velocity <= 0
                and (not self.__y_previous > self.__y + hit_offsets["bottom"])
            ):
                self.__y += hit_offsets["bottom"]
                self.__y_velocity = self.__height_of_jump
                self.__double_jump_is_active = False
                self.__falling = False
                inputs["is_jumping"] = False
                inputs["is_double_jumping"] = False
            else:
                self.__y_velocity -= self.__gravity
        else:
            # If not jumping or falling, only obtain collision offsets for
            # side collisions (see directly below)
            hit_offsets = self.__collision(platform_data)

        # Situation when hitting a platform with the robot's left side
        if (
            hit_offsets["left"] != 0
            and self.__x_velocity < 0
            and (not self.__x_previous < self.__x + hit_offsets["left"])
        ):
            # The hit offset is added to the x coordinate to prevent clipping
            # In this case the offset will be a positive value, moving the robot
            # to the right. This happens before the frame is generated, so it is
            # not seen!
            self.__x += hit_offsets["left"]
            # Velocity is inverted for the bump animation
            self.__x_velocity = -self.__x_velocity
            # Increase the bump animation frames
            self.__x_bump = self.__x_bump_max
        # Situation when hitting a platform with the robot's right side
        if (
            hit_offsets["right"] != 0
            and self.__x_velocity > 0
            and (not self.__x_previous > self.__x + hit_offsets["right"])
        ):
            # In this case the offset will be a negative value, moving the robot
            # to the left.
            self.__x += hit_offsets["right"]
            self.__x_velocity = -self.__x_velocity
            self.__x_bump = self.__x_bump_max

        # Don't move beyond the horizontal borders of the window
        if self.__x <= 0:
            self.__x = 0
        elif self.__x >= self.__window_width - self.__robot.get_width():
            self.__x = self.__window_width - self.__robot.get_width()
        # Set previous horizontal velocity as current (previous velocity
        # is used to calculate the current velocity above in some cases,
        # e.g. in self.__deceleration())
        self.__previous_x_velocity = self.__x_velocity
        # Set previous coordinates as current for next move() call
        self.__x_previous = self.__x
        self.__y_previous = self.__y

    def __base_movement_speed(self, to_left: bool, to_right: bool):
        # This method determines the base movement speed in the horizontal plane
        speed_l = 0.0
        speed_r = 0.0
        # If pressing left on keyboard and not outside left border, move with speed 2 to the left
        if to_left:
            speed_l = -3.0
        # If pressing right on keyboard and not outside right border, move with speed 2 to the right
        if to_right:
            speed_r = 3.0
        # Return the 'vector' of both speeds. If both keys are being pressed, they will cancel each other out
        return speed_l + speed_r

    def __running_speed(self, to_left: bool, to_right: bool, is_running: bool):
        # This method determines the contribution of running to the total movement speed in the horizontal plane
        speed_l = 0.0
        speed_r = 0.0
        # If running, the speed in the given direction is increased by 1
        if to_left and is_running:
            speed_l = -1.0
        if to_right and is_running:
            speed_r = 1.0
        return speed_l + speed_r

    def __jump_x_velocity(self, to_left: bool, to_right: bool):
        # This method determines the contribution of jumping to the total movement speed in the horizontal plane
        speed_l = -1 if to_left else 0
        speed_r = 1 if to_right else 0
        return speed_l + speed_r

    def __deceleration(self):
        # After releasing the left and right movement keys, the robot doesn't abruptly stop, but decelerates to a halt.
        # This method determines the speed while decelerating (i.e. when neither left nor right is pressed), based on
        # the previous velocity in the horizontal plane.
        speed_l = 0.0
        speed_r = 0.0
        decel_amount = 0.25
        # If previously moving to the left and no key is pressed, decrease speed by 0.25 per frame
        if self.__previous_x_velocity < 0:
            speed_l = self.__previous_x_velocity + decel_amount
        # Else if previously moving to the right and no key is pressed, decrease speed by 0.25 per frame
        elif self.__previous_x_velocity > 0:
            speed_r = self.__previous_x_velocity - decel_amount
        return speed_l + speed_r

    def __total_x_velocity(self, inputs: dict):
        # fmt: off
        x_velocity = self.__base_movement_speed(inputs["to_left"], inputs["to_right"])
        x_velocity += self.__running_speed(inputs["to_left"], inputs["to_right"], inputs["is_running"])
        if inputs["is_jumping"]: 
            x_velocity += self.__jump_x_velocity(inputs["to_left"], inputs["to_right"])
        if not inputs["to_left"] and not inputs["to_right"]:
            x_velocity += self.__deceleration()
        # fmt: on
        return x_velocity

    def get_hitbox(self):
        # Create a hitbox (rectangle object) on the position. This method is called upon
        # by other objects in the game for hit detection.
        robot_hitbox = self.__robot.get_rect(topleft=(self.__x, self.__y))
        # Update hitbox size and position for hit detection that corresponds
        # better with the robot.png image (there are some empty pixels in the image)
        robot_hitbox = robot_hitbox.inflate(-12, -10).move(0, 5)
        return robot_hitbox

    def __collision(self, hitbox_data: list):
        # Get robot hitbox
        robot_hitbox = self.get_hitbox()
        # Setting the y-offset to standard 0
        # Dict with the 4 directions. If the value is 0, no hit has been detected.
        # If a hit has been detected, the value is set to the offset in pixels.
        hit_offsets = {"left": 0, "right": 0, "top": 0, "bottom": 0}

        for platform in hitbox_data:
            # Create rectangle object
            platform_hitbox = pygame.Rect(platform)

            # Save platform border variables, format (x1, y1, x2, y2)
            # fmt: off
            platform_left_border = (platform_hitbox.left, platform_hitbox.top, platform_hitbox.left, platform_hitbox.bottom)
            platform_right_border = (platform_hitbox.right, platform_hitbox.top, platform_hitbox.right, platform_hitbox.bottom)
            platform_top_border = (platform_hitbox.left, platform_hitbox.top, platform_hitbox.right, platform_hitbox.top)
            platform_bottom_border = (platform_hitbox.left, platform_hitbox.bottom, platform_hitbox.right, platform_hitbox.bottom)
            # fmt: on

            # If the robot's left side is clipping the platform hitbox
            if robot_hitbox.clipline(platform_right_border):
                hit_offsets["left"] = platform_hitbox.right - robot_hitbox.left
            # If the robot's right side is clipping the platform hitbox
            if robot_hitbox.clipline(platform_left_border):
                hit_offsets["right"] = platform_hitbox.left - robot_hitbox.right
            # If the robot's top side is clipping the platform hitbox
            if robot_hitbox.clipline(platform_bottom_border):
                hit_offsets["top"] = platform_hitbox.bottom - robot_hitbox.top
            # If the robot's bottom side is clipping the platform hitbox
            if robot_hitbox.clipline(platform_top_border):
                hit_offsets["bottom"] = platform_hitbox.top - robot_hitbox.bottom

            # NOTE IF directionsleft == directions right, nothing happens in x direction!

        return hit_offsets

    def dead(self, hit_monster: bool):
        # Simple death condition: if robot falls below
        # the bottom border of the window, or hits a monster,
        # dead = True
        if (self.__y > self.__window_height) or hit_monster:
            return True
        return False

    def reset(self):
        # Reset robot to starting position after game over
        self.__x = 0
        self.__y = self.__y_initial
        self.__x_previous = self.__x
        self.__y_previous = self.__y
        self.__previous_x_velocity = 0
        self.__x_velocity = 0
        self.__y_velocity = self.__height_of_jump
        self.__double_jump_is_active = False
        self.__x_bump = 0
        self.__falling = False
        self.__spawning = True


class Coin:
    def __init__(self, window: pygame.surface.Surface, coordinates: tuple):
        # Create coin image
        self.__coin = pygame.image.load("coin.png")
        # Setting window
        self.__window = window
        # Set coordinates
        self.__x = coordinates[0]
        self.__y = coordinates[1]
        # Grabbed variable
        self.__grabbed = False
        # Velocity of coin after being grabbed
        self.__y_velocity = 2
        # Start color of coin overlay for animation
        self.__color = pygame.Color(0)
        self.__lightness = 100
        self.__color.hsla = (1, 0, self.__lightness, 100)

    @property
    def grabbed(self):
        return self.__grabbed

    def __collision(self, robot: Robot):
        robot_hitbox = robot.get_hitbox()
        coin_hitbox = self.__coin.get_rect(topleft=(self.__x, self.__y))
        if robot_hitbox.colliderect(coin_hitbox):
            return True
        return False

    def __grabbed_animation(self):
        # Creates animation for the coin after it has been grabbed by
        # the player.
        if self.__y > -100:
            self.__y -= self.__y_velocity

        # Set color and increase lightness for next frame
        self.__color.hsla = (1, 0, self.__lightness, 100)
        self.__lightness = self.__lightness - 2.5 if self.__lightness > 0 else 0
        # Create fade mask rectangle and fill with color
        fade_mask = pygame.Surface(self.__coin.get_size())
        fade_mask.fill(self.__color)
        # Display fade mask over coin image (with blend mode MULTIPLY)
        coin = pygame.image.load("coin.png")
        coin.blit(fade_mask, (0, 0), special_flags=pygame.BLEND_MULT)
        # Display the resulting coin image
        self.__window.blit(coin, (self.__x, self.__y))

    def place(self, robot: Robot):
        # Check if robot hitbox collides with coin hitbox
        if not self.__grabbed:
            self.__grabbed = self.__collision(robot)
            # Display coin in the window
            self.__window.blit(self.__coin, (self.__x, self.__y))
        else:
            # Get the fade-out animation rectangle
            self.__grabbed_animation()


class Portal:
    def __init__(self, window: pygame.surface.Surface, coordinates: tuple):
        # Create portal image
        self.__portal = pygame.image.load("door.png")
        # Setting window
        self.__window = window
        # Set coordinates
        self.__x = coordinates[0]
        self.__y = coordinates[1]
        # Bool that states whether or not robot entered portal
        self.__entered = False
        # Start color of coin overlay for animation
        self.__color = pygame.Color(0)
        self.__lightness = 0
        self.__color.hsla = (1, 0, self.__lightness, 100)

    @property
    def entered(self):
        return self.__entered

    def __collision(self, robot: Robot):
        # Get robot hitbox
        robot_hitbox = robot.get_hitbox()
        # Create portal rectangle overlapping portal image
        portal_hitbox = self.__portal.get_rect(topleft=(self.__x, self.__y))
        # Save center to variable
        portal_center = portal_hitbox.center
        # Resize hitbox (we want the player to get into the center of the portal
        # in order to enter it) and set the center to the var saved above
        portal_hitbox.width = 15
        portal_hitbox.height = 20
        portal_hitbox.center = portal_center
        # Return True when robot collides, False if not
        if robot_hitbox.colliderect(portal_hitbox):
            return True
        return False

    def __open_animation(self):
        # Set color and increase lightness for next frame
        self.__color.hsla = (1, 0, self.__lightness, 100)
        self.__lightness = self.__lightness + 1 if self.__lightness < 100 else 100
        # Create fade mask rectangle and fill with color
        fade_mask = pygame.Surface(self.__portal.get_size())
        fade_mask.fill(self.__color)
        # Display fade mask on the portal image with blend mode MULTIPLY
        # Need to reload the portal image with every iteration. Using self.__portal
        # every time would result in multiple overlaps with the mask.
        portal = pygame.image.load("door.png")
        portal.blit(fade_mask, (0, 0), special_flags=pygame.BLEND_MULT)
        # Display resulting portal image
        self.__window.blit(portal, (self.__x, self.__y))

    def place(self, robot: Robot):
        # If robot hasn't entered, self.__entered stays False. Once
        # robot has entered, it stays True
        if not self.__entered:
            self.__entered = self.__collision(robot)
        # If animation hasn't terminated (lightness < 100), keep playing
        # the fade-in animation
        if self.__lightness < 100:
            self.__open_animation()
        # After it has terminated, simply display the portal
        else:
            self.__window.blit(self.__portal, (self.__x, self.__y))


class Monster:
    def __init__(self, window: pygame.surface.Surface, coords_and_velocity: list):
        # Create monster image
        self.__monster = self.__load_monster()
        # Create window
        self.__window = window
        # Coordinates: start of path
        self.__x1 = coords_and_velocity[0][0]
        self.__y1 = coords_and_velocity[0][1]
        # Coordinates: end of path
        self.__x2 = coords_and_velocity[1][0]
        self.__y2 = coords_and_velocity[1][1]
        # Velocity
        self.__velocity = coords_and_velocity[2]
        # Initial coordinates set as floats
        self.__x = float(self.__x1)
        self.__y = float(self.__y1)
        # Path length
        self.__path_length = math.sqrt(
            (self.__x2 - self.__x1) ** 2 + (self.__y2 - self.__y1) ** 2
        )
        # x and y velocity calculation
        if self.__path_length > 0:
            self.__x_velocity = (
                (self.__x2 - self.__x1) * self.__velocity
            ) / self.__path_length
            self.__y_velocity = (
                (self.__y2 - self.__y1) * self.__velocity
            ) / self.__path_length
        else:
            self.__x_velocity = 0
            self.__y_velocity = 0

    def __load_monster(self):
        # This method puts a white line around the monster so it is visible on a black
        # background
        monster = pygame.image.load("monster.png")
        # Load the image a second time
        inverted_monster = pygame.image.load("monster.png")
        # Create white inversion mask the size of the monster image that's to be
        # inverted
        inversion_mask = pygame.Surface(inverted_monster.get_rect().size)
        inversion_mask.fill((255, 255, 255))
        # Invert the image
        inverted_monster.blit(inversion_mask, (0, 0), special_flags=pygame.BLEND_ADD)
        # Make it larger so lines would be visible
        inverted_monster = pygame.transform.scale(
            inverted_monster,
            (inverted_monster.get_width() * 1.10, inverted_monster.get_height() * 1.05),
        )
        # Display the original monster on the inverted one with slight offset, so lines around it
        # are visible
        inverted_monster.blit(monster, (3, 2))

        return inverted_monster

    def __monster_image(self):
        # This flips the monster horizontally depending on x-velocity
        monster = self.__monster
        if self.__x_velocity < 0:
            monster = pygame.transform.flip(monster, True, False)
        return monster

    def collision(self, robot: Robot):
        # Get robot hitbox
        robot_hitbox = robot.get_hitbox()
        # Create portal rectangle overlapping portal image
        monster_hitbox = self.__monster.get_rect(topleft=(self.__x, self.__y))
        # Save center to variable
        monster_center = monster_hitbox.center
        # Resize hitbox (we want the player to get into the center of the portal
        # in order to enter it) and set the center to the var saved above
        monster_hitbox.width = 38
        monster_hitbox.height = 64
        monster_hitbox.center = monster_center
        # Return True when robot collides, False if not
        if robot_hitbox.colliderect(monster_hitbox):
            return True
        return False

    def __get_next_coordinates(self):
        # Get next x coordinate
        if self.__x1 < self.__x2:
            if (self.__x + self.__x_velocity) >= self.__x2:
                self.__x = self.__x2
                self.__x_velocity = -self.__x_velocity
            elif (self.__x + self.__x_velocity) <= self.__x1:
                self.__x = self.__x1
                self.__x_velocity = -self.__x_velocity
            else:
                self.__x += self.__x_velocity
        elif self.__x2 < self.__x1:
            if (self.__x + self.__x_velocity) >= self.__x1:
                self.__x = self.__x1
                self.__x_velocity = -self.__x_velocity
            elif (self.__x + self.__x_velocity) <= self.__x2:
                self.__x = self.__x2
                self.__x_velocity = -self.__x_velocity
            else:
                self.__x += self.__x_velocity
        # Get next y coordinate
        if self.__y1 < self.__y2:
            if (self.__y + self.__y_velocity) >= self.__y2:
                self.__y = self.__y2
                self.__y_velocity = -self.__y_velocity
            elif (self.__y + self.__y_velocity) <= self.__y1:
                self.__y = self.__y1
                self.__y_velocity = -self.__y_velocity
            else:
                self.__y += self.__y_velocity
        elif self.__y2 < self.__y1:
            if (self.__y + self.__y_velocity) >= self.__y1:
                self.__y = self.__y1
                self.__y_velocity = -self.__y_velocity
            elif (self.__y + self.__y_velocity) <= self.__y2:
                self.__y = self.__y2
                self.__y_velocity = -self.__y_velocity
            else:
                self.__y += self.__y_velocity

    def place(self):
        # Coordinates need to be set to int because x- and y-velocities will
        # always be floats
        self.__window.blit(self.__monster_image(), (int(self.__x), int(self.__y)))
        self.__get_next_coordinates()


class Game:
    def __init__(self):
        pygame.init()

        # Setting up the window
        self.window_height = 720
        self.window_width = 1280
        self.window = pygame.display.set_mode((self.window_width, self.window_height))

        # Setting up a new game
        self.level = 1
        self.total_levels = 10
        self.won = False  # win status
        self.new_game()

        # Controls of the game
        self.controls = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "run": pygame.K_w,
            "jump": pygame.K_SPACE,
            "pause": pygame.K_ESCAPE,
            "start": pygame.K_RETURN,
            "controls": pygame.K_c,
            "tutorials": pygame.K_t,
        }

        # Control menu texts
        self.controls_menu_texts = [
            ["Controls:", ""],
            ["'a'", "move left"],
            ["'d'", "move right"],
            ["'w'", "sprint"],
            ["'Space'", "jump / double jump"],
            ["'Esc'", "pause game"],
            ["'t'", "toggle in-game tutorials"],
            ["Press 'Esc' to return ...", ""],
        ]

        # Clock
        self.clock = pygame.time.Clock()
        self.fps = 60

        # Setup of game fonts
        self.font1 = pygame.font.SysFont("Arial", 18)
        self.font2 = pygame.font.SysFont("Arial", 24)
        self.menu_text_font = pygame.font.SysFont("Arial", 26)
        self.menu_title_font = pygame.font.SysFont("Arial", 36)
        # X-position for menu texts
        self.x_txt = (self.window_width / 2) - 200

        # Title of game
        self.game_title = "JUMPBOT"

        # Setting game name in caption
        pygame.display.set_caption(self.game_title)

        # Initial game over status
        self.game_over = False

        # Turn off/on visibility of hitboxes for testing
        self.display_hitboxes = False

        # Tutorial text list
        self.tutorial_texts = [
            "Instructions:",
            "Collect all coins to open the portal.",
            "Enter the portal to go to the next level.",
            "Avoid gaps and monsters.",
            "Press 'c' to show controls.",
            "Press 'a' to move left and 'd' to move right ... (press 't' to toggle tutorials)",
            "... and press 'Space' to jump.",
            "Now enter the portal and gain a life ♥",
            "Press 'Space' twice to double jump.",
            "Avoid gaps. Hold 'w' to sprint.",
            "Avoid monsters.",
        ]

        # When this object is made, the game starts by initiating the main loop
        self.main_loop()

    def new_game(self):
        # Getting the level dictionary
        level = self.levels(self.level)

        # Platform data stored in self.map
        self.map = level["platforms"]

        # Coin data stored in self.coins
        self.coins = [Coin(self.window, position) for position in level["coins"]]

        # Monster creation
        self.monsters = [
            Monster(self.window, position) for position in level["monsters"]
        ]

        # Bool that indicates whether or not robot hit a monster in last frame
        self.hit_monster = False

        # Portal creation
        self.portal = Portal(self.window, level["portal"])

        # Number of player lives is equal to 3 when starting a new
        # game (i.e. self.level == 1), but doesn't change
        # when not starting a new game (i.e. self.level > 1)
        self.lives = 3 if self.level == 1 else self.lives

        # Create playable robot object.
        self.robot = Robot(self.window)

        # Pause status of the game
        self.paused = False

        # Game inputs. Set to false at the start of every game.
        self.inputs = {
            "to_left": False,
            "to_right": False,
            "is_running": False,
            "is_jumping": False,
            "is_double_jumping": False,
            "pause_status_change": False,
            "game_started": False if self.level == 1 else True,
            "show_controls": False,
            "show_tutorials": True
            if self.level == 1
            else self.inputs["show_tutorials"],
        }

    def levels(self, level: int):
        # The levels list contains a dictionary of levels
        # Every map has 5 "platform levels", separated by the same y-value
        # (in self.build_world()),
        # at which tiles can be placed. The map consists of a dictionary,
        # where each level is represented as a key, starting at the
        # lowest level. Lists are of variable size. They always start with
        # the number of pixels preceding the first tile unit. If nothin follows,
        # there are no tiles on this level. The next index is the number of tile
        # units (as called in self.building_unit()). If nothing follows, the
        # list contains no other values. Otherwise it has the structure:
        # [pixels, build_units, pixels, build_units, ...]
        # N.B. make sure the lowet level always has [0, 1 or higher, ...] at the
        # start, because of the robot spawn position!!!

        # Coin lists contain the coordinates for coin spawns.
        # Monster lists contain lists with two coordinates per monster
        # (it patrols between these), along with its velocity:
        # [..., [(x1, y1), (x2, y2), v], ...]
        # Portal contains the portal coordinates (shows when coins are collected)

        levels = [
            # TEST LEVEL 0
            {
                "platforms": [[0, 3, 200, 3], [0], [0], [0], [0]],
                "coins": [(500, 500), (120, 600), (800, 450)],
                "monsters": [[(0, 0), (0, 0), 0]],
                "portal": (600, 100),
            },
            # LEVEL 1
            {
                "platforms": [[0, 12], [0], [0], [0], [0]],
                "coins": [(500, 600), (120, 600), (800, 500)],
                "monsters": [],
                "portal": (1150, 575),
            },
            # LEVEL 2
            {
                "platforms": [[0, 12], [0], [300, 3], [0], [0]],
                "coins": [(450, 200), (120, 600), (1100, 450)],
                "monsters": [],
                "portal": (500, 320),
            },
            # LEVEL 3
            {
                "platforms": [
                    [0, 1, 150, 2, 300, 2],
                    [1200, 1],
                    [0],
                    [820, 3],
                    [500, 1],
                ],
                "coins": [(900, 600), (1224, 400), (850, 100)],
                "monsters": [],
                "portal": (520, 100),
            },
            # LEVEL 4
            {
                "platforms": [
                    [0, 2, 250, 9],
                    [0],
                    [700, 3],
                    [500, 1],
                    [0],
                ],
                "coins": [(900, 600), (320, 400), (500, 200)],
                "monsters": [[(600, 600), (1200, 600), 2], [(700, 300), (700, 100), 1]],
                "portal": (300, 650),
            },
            # LEVEL 5
            {
                "platforms": [
                    [0, 5, 150, 5],
                    [120, 1, 880, 1],
                    [250, 3, 150, 3],
                    [0, 1, 150, 7, 150, 1],
                    [0],
                ],
                "coins": [(100, 300), (380, 360), (890, 360), (1120, 480)],
                "monsters": [
                    [(250, 360), (1000, 360), 2],
                    [(110, 460), (110, 100), 2],
                    [(1110, 100), (1110, 460), 2],
                ],
                "portal": (630, 220),
            },
            # LEVEL 6
            {
                "platforms": [
                    [0, 1, 250, 1, 700, 2],
                    [130, 2, 140, 2],
                    [380, 1, 260, 1],
                    [520, 2, 250, 1],
                    [0, 4, 700, 2],
                ],
                "coins": [(20, 130), (250, 240), (900, 10), (1200, 600), (570, 420)],
                "monsters": [
                    [(0, 120), (400, 120), 3],
                    [(250, 600), (1000, 100), 2],
                    [(1000, 600), (240, 240), 2],
                ],
                "portal": (950, 600),
            },
            # LEVEL 7
            {
                "platforms": [
                    [0, 1, 150, 1, 600, 1],
                    [180, 1, 400, 1],
                    [0, 1, 1000, 2],
                    [800, 3],
                    [180, 1, 850, 2],
                ],
                "coins": [(550, 250), (990, 590), (1200, 50), (180, 50)],
                "monsters": [
                    [(750, 230), (1100, 230), 1],
                    [(0, 25), (1220, 25), 6],
                    [(350, 350), (550, 650), 2],
                ],
                "portal": (270, 580),
            },
            # LEVEL 8
            {
                "platforms": [
                    [0, 1, 250, 1, 250, 1, 250, 1],
                    [1270, 1],
                    [374, 1, 250, 1, 250, 1],
                    [150, 1],
                    [374, 1, 250, 1, 250, 1],
                ],
                "coins": [
                    (375, 600),
                    (740, 600),
                    (1110, 600),
                    (375, 360),
                    (740, 360),
                    (1110, 360),
                    (375, 120),
                    (740, 120),
                    (155, 240),
                ],
                "monsters": [
                    [(730, 0), (730, 650), 3],
                    [(730, 0), (80, 650), 3],
                    [(730, 0), (1110, 650), 3],
                ],
                "portal": (1110, 100),
            },
            # LEVEL 9
            {
                "platforms": [
                    [0, 1, 300, 4],
                    [0],
                    [620, 1],
                    [400, 1, 340, 1],
                    [0, 1, 1120, 1],
                ],
                "coins": [(10, 100), (1230, 100), (400, 220), (860, 220)],
                "monsters": [
                    [(0, 340), (540, 340), 8],
                    [(540, 340), (0, 340), 8],
                    [(200, 0), (200, 650), 8],
                    [(1240, 340), (700, 340), 8],
                    [(700, 340), (1240, 340), 8],
                    [(1050, 650), (1050, 0), 8],
                ],
                "portal": (600, 580),
            },
            # LEVEL 10
            {
                "platforms": [
                    [0, 5, 530, 1],
                    [-60, 5],
                    [124, 4, 670, 1],
                    [-60, 5],
                    [124, 4, 300, 1, 250, 1],
                ],
                "coins": [(520, 600), (130, 360), (1240, 360), (910, 120)],
                "monsters": [
                    [(300, 600), (1200, 600), 3],
                    [(0, 480), (900, 480), 2],
                    [(60, 360), (1200, 360), 4],
                    [(900, 240), (0, 240), 2],
                    [(1200, 120), (60, 120), 4],
                ],
                "portal": (800, 550),
            },
        ]

        return levels[level]

    def main_loop(self):
        # Main game loop. Check for events (mainly keyboard inputs)
        # and draw the frames in the window in reaction to the inputs
        # Keeps looping until the game is closed.
        while True:
            self.check_events()
            self.draw_window()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == self.controls["move_left"]:
                    self.inputs["to_left"] = True
                if event.key == self.controls["move_right"]:
                    self.inputs["to_right"] = True
                if event.key == self.controls["run"]:
                    self.inputs["is_running"] = True
                if event.key == self.controls["jump"]:
                    if not self.inputs["is_jumping"]:
                        self.inputs["is_jumping"] = True
                    elif (
                        self.inputs["is_jumping"]
                        and not self.inputs["is_double_jumping"]
                    ):
                        self.inputs["is_double_jumping"] = True
                if event.key == self.controls["pause"]:
                    self.inputs["pause_status_change"] = True
                # Read this input only when game_started == False, meaning
                # we are in the start menu (which happens when starting
                # the game or after a game over)
                # This ensures this status doesn't change during gameplay
                # Also resets game over status
                if (
                    event.key == self.controls["start"]
                    and not self.inputs["game_started"]
                ):
                    self.inputs["game_started"] = True
                    self.game_over = False
                    self.won = False
                    # Set paused to False in case user pressed 'Esc' in start
                    # menu. This way a new game won't start with a pause menu
                    self.paused = False
                    self.inputs["pause_status_change"] = False
                # Key press to show controls, only when in start or pause menu
                if event.key == self.controls["controls"] and (
                    not self.inputs["game_started"] or self.paused
                ):
                    self.inputs["show_controls"] = True
                # Key press to toggle tutorial text in-game, only when not in start
                # or pause menu
                if event.key == self.controls["tutorials"] and not (
                    not self.inputs["game_started"] or self.paused
                ):
                    if self.inputs["show_tutorials"]:
                        self.inputs["show_tutorials"] = False
                    else:
                        self.inputs["show_tutorials"] = True

            if event.type == pygame.KEYUP:
                if event.key == self.controls["move_left"]:
                    self.inputs["to_left"] = False
                if event.key == self.controls["move_right"]:
                    self.inputs["to_right"] = False
                if event.key == self.controls["run"]:
                    self.inputs["is_running"] = False

            if event.type == pygame.QUIT:
                exit()

    def start_menu(self):
        # Color of text
        title_color = (255, 255, 0)
        game_over_color = (255, 0, 0)
        text_color = (255, 255, 255)
        won_color = (0, 255, 0)
        # Text strings
        line1 = "Press 'Enter' to start a new game."
        line2 = "Press 'c' to view game controls."
        # Render texts
        title = self.menu_title_font.render(self.game_title, True, title_color)
        go = self.menu_title_font.render("GAME OVER!", True, game_over_color)
        won = self.menu_title_font.render("YOU WON!!!", True, won_color)
        text1 = self.menu_text_font.render(line1, True, text_color)
        text2 = self.menu_text_font.render(line2, True, text_color)
        # Display texts
        self.window.blit(title, (self.x_txt, 100))
        if self.game_over:
            self.window.blit(go, (self.x_txt + 200, 100))
        elif self.won:
            self.window.blit(won, (self.x_txt + 200, 100))
        self.window.blit(text1, (self.x_txt, 200))
        self.window.blit(text2, (self.x_txt, 250))
        self.basic_instructions(y_offset=330)
        # Get robot image to display large next on start menu page
        robot_image = pygame.image.load("robot.png")
        robot_image = pygame.transform.scale(
            robot_image, (robot_image.get_width() * 5, robot_image.get_height() * 5)
        )
        self.window.blit(robot_image, (100, 100))

    def controls_menu(self):
        text_color = (255, 255, 255)
        # List of text renders
        text_renders = [
            [
                self.menu_text_font.render(line[0], True, text_color),
                self.menu_text_font.render(line[1], True, text_color),
            ]
            for line in self.controls_menu_texts
        ]
        # Display texts
        y_pos = 200  # y-position of first line of text
        for i in range(len(text_renders)):
            self.window.blit(text_renders[i][0], (self.x_txt, y_pos))
            self.window.blit(text_renders[i][1], (self.x_txt + 150, y_pos))
            increment = 50 if i in [0, len(text_renders) - 2] else 30
            y_pos += increment

    def basic_instructions(self, y_offset: int):
        # Text_color
        text_color = (150, 150, 150)
        # List of text renders
        text_renders = [
            self.font2.render(self.tutorial_texts[i], True, text_color)
            for i in range(5)
        ]
        # Display texts
        for i in range(5):
            # Don't display this line when in the main menu
            if not self.inputs["game_started"] and i == 4:
                continue
            self.window.blit(text_renders[i], (self.x_txt, y_offset))
            increment = 40 if i == 0 else 30
            y_offset += increment

    def draw_block(self, block: str, topleft: tuple):
        # Draws the different building blocks used to create the level.
        # Imported x and y offsets
        x, y = topleft

        # Colors
        outline_color = (0, 0, 0)
        brick_front_color = (153, 76, 0)
        brick_side_color = (102, 51, 0)
        tile_front_color = (150, 150, 150)
        tile_surface_color = (181, 181, 181)
        tile_side_color = (125, 125, 125)

        # Dimensions
        brick_width = 31
        brick_height = 15
        brick_half_width = round(brick_width / 2)
        tile_width = 121
        tile_height = 5

        # Blocks dictionary, containing type [index 0], color [index 1],
        # and dimension list [index 2: left, top, width, height]
        # Type "r" = rectangle, type "p" = polygon
        # fmt: off
        blocks = {
            "full_brick": ["r", brick_front_color, [x, y, brick_width, brick_height]],
            "half_brick": ["r", brick_front_color, [x, y, brick_half_width, brick_height]],
            "brick_side": ["p", brick_side_color, [(x + brick_half_width, y), (x, y + brick_half_width), (x, y + brick_half_width + 14), (x + brick_half_width, y + 14)]],
            "brick_half_side": ["p", brick_side_color, [(x + (brick_half_width / 2), y), (x, y + (brick_half_width / 2)), (x, y + (brick_half_width / 2) + 14), (x + (brick_half_width / 2), y + 14)]],
            "tile_front": ["r", tile_front_color, [x, y, tile_width, tile_height]],
            "tile_surface": ["p", tile_surface_color, [(x + brick_width, y), (x, y + brick_width), (x + tile_width, y + brick_width), (x + tile_width + brick_width, y)]],
            "tile_side": ["p", tile_side_color, [(x + brick_width, y), (x, y + brick_width), (x, y + brick_width + 4), (x + brick_width, y + 4)]],
            "side_visual_fix": ["r", outline_color, [x, y, 1, 33]],
        }
        # fmt: on

        if blocks[block][0] == "r":
            pygame.draw.rect(self.window, blocks[block][1], blocks[block][2])
            pygame.draw.rect(self.window, outline_color, blocks[block][2], width=1)
        else:
            pygame.draw.polygon(self.window, blocks[block][1], blocks[block][2])
            pygame.draw.polygon(self.window, outline_color, blocks[block][2], width=1)

    def draw_platform(self, length: int, topleft: tuple):
        # Draws an entire platform calling on self.draw_block() in the
        # correct order, with correct input coordinates.
        # Set starting x and y topleft coordinates, as input from map data
        # inside self.build_world()
        x_start, y_start = topleft

        # Construct the platform, looping through the range of platform length
        for i in range(length):
            unit_length = 120 * i
            # fmt: off
            # Draw the starting unit of the platform
            if i == 0:
                self.draw_block("tile_surface", (x_start - 1 + unit_length, y_start))
                self.draw_block("tile_front", (x_start + unit_length, y_start + 31))
                self.draw_block("half_brick", (x_start + unit_length, y_start + 35))
                for j in range(3):
                    self.draw_block("full_brick", (x_start + 15 + (30 * j) + unit_length, y_start + 35))
                for j in range(4):
                    self.draw_block("full_brick", (x_start + (30 * j) + unit_length, y_start + 49))
            # Draw middle units of the platform
            else:
                self.draw_block("tile_surface", (x_start - 1 + unit_length, y_start))
                self.draw_block("tile_front", (x_start + unit_length, y_start + 31))
                for j in range(-1, 3):
                    self.draw_block("full_brick", (x_start + 15 + (30 * j) + unit_length, y_start + 35))
                for j in range(4):
                    self.draw_block("full_brick", (x_start + (30 * j) + unit_length, y_start + 49))
            # If i is at the end of the length range, draw the end of the platform
            if i == length - 1:
                self.draw_block("tile_side", (x_start + 120 + unit_length, y_start))
                self.draw_block("half_brick", (x_start + 105 + unit_length, y_start + 35))
                self.draw_block("brick_side", (x_start + 120 + unit_length, y_start + 19))
                self.draw_block("brick_side", (x_start + 136 + unit_length, y_start + 3))
                self.draw_block("brick_half_side", (x_start + 120 + unit_length, y_start + 41))
                self.draw_block("brick_side", (x_start + 128 + unit_length, y_start + 25))
                self.draw_block("brick_half_side", (x_start + 144 + unit_length, y_start + 17))
                self.draw_block("side_visual_fix", (x_start + 151 + unit_length, y_start))
            # fmt: on

    def build_world(self):
        # This method creates the game world. Map data is stored in self.map.
        # This data is used to draw platforms with (using method
        # self.draw_platform()). Meanwhile, it defines the hitboxes of all
        # platforms, using the map data (from which we can derive the number
        # of platforms created at a certain x,y-coordinate)

        # List that contains dimensional info needed to create hitboxes of the
        # platforms in the world. The info is saved as [x, y, width, height].
        # This data will get returned, so it can be accessed by the player-
        # controlled robot to check for collision with the platforms.
        hitbox_data = []

        # Construct the level from the information contained in self.map
        # Loops through all 'level's inside map, the structure of which
        # is discussed inside method self.new_game().
        for level in range(len(self.map)):
            # Always start outside of the map (x = -60), so the first platform
            # can pass through the left border of the window.
            x = -60
            # The levels are separated by 120 pixels in height. The thickness
            # of the platform is a little under 70 pixels (so the first level
            # floats slightly above the bottom border of the window)
            y = self.window_height - 70 - (level * 120)
            # Loop through the elements of the levels
            for i in range(len(self.map[level])):
                # Every even index counts the number of pixels between
                # platforms
                if i % 2 == 0:
                    # Update the x coordinate with this number of pixels
                    x += self.map[level][i]
                # Uneven index contains a number of adjacent platform units
                else:
                    # Save hitbox dimensions in a tuple, which is then appended to
                    # the hitbox data list
                    hitbox_dimensions = (x + 15, y + 15, self.map[level][i] * 122, 35)
                    hitbox_data.append(hitbox_dimensions)
                    # Draw the platform. The argument self.map[level][i] will input
                    # the number of adjacent platform units into self.draw_platform()
                    self.draw_platform(self.map[level][i], (x, y))
                    # Update the x coordinate with the number of platform units
                    # multiplied by platform width (120 pixels)
                    x += self.map[level][i] * 120

        return hitbox_data

    def display_score(self, coin_count: int):
        # Color of the text
        number_color = (255, 255, 255)
        # Coin image, which is then made smaller
        coin_image = pygame.image.load("coin.png")
        small_coin = pygame.transform.smoothscale(
            coin_image, (coin_image.get_width() * 0.5, coin_image.get_height() * 0.5)
        )
        # Text: shows amount of collected coins / total collectable coins
        # (for the current level)
        score_text = self.font1.render(
            f"{coin_count}/{len(self.coins)}", True, number_color
        )
        # Display the number of coins that have been collected
        # next to a small coin icon.
        self.window.blit(score_text, (45, 45))
        self.window.blit(small_coin, (20, 45))

    def display_lives(self):
        # Color of text
        lives_color = (255, 0, 0)
        # Text
        lives_text = self.font1.render(f"{self.lives}", True, lives_color)
        heart = self.font2.render("♥", True, lives_color)
        # Display the text
        self.window.blit(heart, (24, 13))
        self.window.blit(lives_text, (45, 18))

    def display_level(self):
        # Color of text
        text_color = (255, 255, 255)
        # Text
        level = self.font1.render(
            f"Level {self.level}/{self.total_levels}", True, text_color
        )
        # Display
        self.window.blit(level, (24, 70))

    def display_tutorials(self, coin_count: int):
        # Tutorial text color
        color = (255, 255, 255)
        # Render tutorial texts
        renders = [
            self.font1.render(self.tutorial_texts[i], True, color)
            for i in range(5, len(self.tutorial_texts))
        ]
        # Get rectangles so tutorial texts can be horizontally centered
        y_pos = 400 if self.level == 3 else 200
        renders_rect = [
            renders[i].get_rect(center=(self.window_width / 2, y_pos))
            for i in range(len(renders))
        ]

        # Display according to level
        if self.level == 1:
            if coin_count < 2:
                self.window.blit(renders[0], renders_rect[0])
            elif coin_count == 2:
                self.window.blit(renders[1], renders_rect[1])
            else:
                self.window.blit(renders[2], renders_rect[2])
        elif self.level == 2:
            self.window.blit(renders[3], renders_rect[3])
        elif self.level == 3:
            self.window.blit(renders[4], renders_rect[4])
        elif self.level == 4:
            self.window.blit(renders[5], renders_rect[5])

    def pause_menu(self):
        # Colors of text
        text_color = (255, 255, 255)
        # Main pause text
        pause_text = "Game paused. Press 'Esc' to continue ..."
        # Render texts
        pause = self.menu_text_font.render(pause_text, True, text_color)
        # Display texts
        self.window.blit(pause, (self.x_txt, 250))
        self.basic_instructions(y_offset=330)

    def pause_handler(self):
        # If the pause key has not been pressed, return the original
        # pause status
        if not self.inputs["pause_status_change"]:
            return self.paused
        # If 'Esc' has been pressed, invert the pause status and set the
        # key press to False. This enables the same key to be used to
        # initiate and end the pause.
        else:
            self.inputs["pause_status_change"] = False
            return not self.paused

    def draw_window(self):
        # Set black background color
        self.window.fill((0, 0, 0))

        # Display start menu when new game starts or game is over
        if not self.inputs["game_started"]:
            if self.inputs["show_controls"]:
                self.controls_menu()
                if self.inputs["pause_status_change"]:
                    self.inputs["pause_status_change"] = False
                    self.inputs["show_controls"] = False
            else:
                self.start_menu()

            pygame.display.flip()
            self.clock.tick(self.fps)
            return

        # Update paused status (but not when showing controls, so
        # 'Esc' can be used to return from the controls menu to the
        # pause menu)
        if not self.inputs["show_controls"]:
            self.paused = self.pause_handler()

        # Check pause status, display pause menu if True
        if self.paused:
            # Show controls menu if 'c' is pressed during the pause,
            # else show pause menu
            if self.inputs["show_controls"]:
                self.controls_menu()
                # If 'Esc' is pressed during active controls menu, return
                # to pause menu in next frame by changing input states
                if self.inputs["pause_status_change"]:
                    self.inputs["pause_status_change"] = False
                    self.inputs["show_controls"] = False
            else:
                self.pause_menu()
            pygame.display.flip()
            self.clock.tick(self.fps)
            return

        # Set game over condition to True if conditions are met
        dead = self.robot.dead(self.hit_monster)

        # Reset robot and inputs if a life is lost. Reset the game if all
        # lives are lost (this will return to start menu because level is
        # set to 1).
        if dead:
            if self.lives > 0:
                # Window flashes slightly red for 1 frame to inform
                # the player a life has been lost
                self.window.fill((100, 0, 0))
                # Subtract one life
                self.lives -= 1
                # Reset hit_monster
                self.hit_monster = False
                # Reset robot and jump inputs
                self.robot.reset()
                self.inputs["is_jumping"] = False
                self.inputs["is_double_jumping"] = False
                # self.inputs["move_left"] = False
                # self.inputs["move_right"] = False
            else:
                # If out of lives, game over, start new game
                self.level = 1
                pygame.time.wait(500)
                # Set game over status to True
                self.game_over = True
                self.new_game()

        # Place coins (robot is input to check for collision)
        for coin in self.coins:
            coin.place(self.robot)

        # Portal is open when sum of grabbed coins is equal to the amount of
        # coins within the level.
        # Get the coin count of the current level
        level_coin_count = sum([coin.grabbed for coin in self.coins])
        open_portal = True if level_coin_count == len(self.coins) else False

        if open_portal:
            self.portal.place(self.robot)
            if self.portal.entered:
                self.lives += 1
                # If self.level = self.total_levels, self.level is reset to 1, meaning
                # new_game will set parameters such that the start menu will appear.
                # Also, self.won is set to True when self.level is equal to 1 (the order
                # of operations ensures this only happens when the level has been equal
                # to total levels, i.e. the highest level). This will allow the appropriate
                # text in the start menu to be displayed.
                self.level = self.level + 1 if self.level < self.total_levels else 1
                self.won = True if self.level == 1 else False
                pygame.time.wait(500)
                self.new_game()

        # Get hitbox data. It should be noted that self.build_world() doesn't
        # only return this data, but also has the side effect of drawing the
        # platforms inside the window. This is done to avoid having to loop
        # through the map data twice.
        hitbox_data = self.build_world()

        # If self.display_hitboxes == True, a red box will be displayed around
        # the hitboxes of the platforms. This is for testing purposes
        if self.display_hitboxes:
            for hitbox in hitbox_data:
                pygame.draw.rect(self.window, (255, 0, 0), hitbox, width=2)
                pygame.draw.rect(
                    self.window, (255, 0, 0), self.robot.get_hitbox(), width=2
                )

        # Display tutorials if they are toggled
        if self.inputs["show_tutorials"] and self.level < 5:
            self.display_tutorials(level_coin_count)

        # Create monsters
        for monster in self.monsters:
            monster.place()
            if monster.collision(self.robot):
                self.hit_monster = True

        # Play the robot. Takes the game inputs and hitbox data as arguments.
        self.robot.play(self.inputs, hitbox_data)

        # Display player lives
        self.display_lives()
        # Display the total coin count
        self.display_score(level_coin_count)
        # Display level
        self.display_level()

        # Generate frame, clock for frame time
        pygame.display.flip()
        self.clock.tick(self.fps)


if __name__ == "__main__":
    Game()
