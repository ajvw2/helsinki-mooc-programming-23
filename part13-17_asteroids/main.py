# I had fun making this exercise and expanded upon it a lot. It has all the functionality
# of the intended exercise and then some more (jumping, double jumping, player lives,
# possibility to pause the game, to restart the game after Game Over, high score system
# that loads the high score from a file, asteroids of randomized sizes and with randomized
# paths, etc.)
import pygame
from random import randint
import numpy as np


class Robot:
    def __init__(self, window: pygame.surface.Surface):
        # Different images of the robot for jumping animations
        self.__robot = pygame.image.load("robot.png")
        self.__robot_jumping_left = pygame.image.load("robot_jumping_l.png")
        self.__robot_jumping_right = pygame.image.load("robot_jumping_r.png")
        # Setting window and determining window sizes
        self.__window = window
        self.__window_w = window.get_width()
        self.__window_h = window.get_height()
        # Setting initial coordinates and separately storing the initial y value for
        # use inside of the jump() function
        self.__x = self.__window_w / 2
        self.__y_initial = self.__window_h - self.__robot.get_height()
        self.__y = self.__y_initial
        # Setting hights for jumps and double jumps separately. Generally, having the
        # double jump value a little higher 'feels' better in this 'game'.
        self.__height_of_jump = 13
        self.__height_of_double_jump = 18
        self.__double_jump_is_active = False
        # Setting initial velocities in both planes, and also the previous velocity in the
        # horizontal plane (for the deceleration function)
        self.__previous_x_velocity = 0
        self.__x_velocity = 0
        self.__y_velocity = self.__height_of_jump

    def play(self, inputs: dict):
        # Main function of the robot. Calls on the move() function which calculates
        # new coordinates and changes input values when necessary
        self.__move(inputs)
        # Plot the image on the screen
        self.__window.blit(
            self.__jump_image(
                inputs["to_left"], inputs["to_right"], inputs["is_jumping"]
            ),
            (self.__x, self.__y),
        )

    def __move(self, inputs: dict):
        # Input is a dict containing 5 boolean values: to_left, to_right, is_running, is_jumping, is_double_jumping
        x_velocity = self.__base_movement_speed(inputs["to_left"], inputs["to_right"])
        x_velocity += self.__running_speed(
            inputs["to_left"], inputs["to_right"], inputs["is_running"]
        )
        x_velocity += self.__jump_x_velocity(
            inputs["to_left"],
            inputs["to_right"],
            inputs["is_jumping"],
            inputs["is_double_jumping"],
        )
        x_velocity += self.__deceleration(inputs["to_left"], inputs["to_right"])
        # Don't move beyond the horizontal borders of the window
        self.__x += x_velocity
        if self.__x <= 0:
            self.__x = 0
        elif self.__x >= self.__window_w - self.__robot.get_width():
            self.__x = self.__window_w - self.__robot.get_width()
        # Set previous horizontal velocity as current
        self.__previous_x_velocity = x_velocity

        # This function changes the y variable and returns jump boolean values (changed or not,
        # dependent on what happens inside jump())
        jump_boolean_values = self.__jump(
            inputs["is_jumping"], inputs["is_double_jumping"]
        )
        # The jump variables are changed in the dictionary thats input
        inputs["is_jumping"] = jump_boolean_values[0]
        inputs["is_double_jumping"] = jump_boolean_values[1]

    def __base_movement_speed(self, to_left: bool, to_right: bool):
        # This function determines the base movement speed in the horizontal plane
        speed_l = 0.0
        speed_r = 0.0
        # If pressing left on keyboard and not outside left border, move with speed 2 to the left
        if to_left:
            speed_l = -2.0
        # If pressing right on keyboard and not outside right border, move with speed 2 to the right
        if to_right:
            speed_r = 2.0
        # Return the 'vector' of both speeds. If both keys are being pressed, they will cancel each other out
        return speed_l + speed_r

    def __running_speed(self, to_left: bool, to_right: bool, is_running: bool):
        # This function determines the contribution of running to the total movement speed in the horizontal plane
        speed_l = 0.0
        speed_r = 0.0
        # If running, the speed in the given direction is increased by 1
        if to_left and is_running:
            speed_l = -1.0
        if to_right and is_running:
            speed_r = 1.0
        return speed_l + speed_r

    def __jump_x_velocity(
        self, to_left: bool, to_right: bool, is_jumping: bool, is_double_jumping: bool
    ):
        # This function determines the contribution of jumping to the total movement speed in the horizontal plane
        speed_l = 0.0
        speed_r = 0.0
        # When moving to the left and jumping, add 0.5 speed in that direction, and add 1.0 when double jumping
        if to_left and is_jumping and not is_double_jumping:
            speed_l = -0.5
        elif to_left and is_double_jumping:
            speed_l = -1.0
        # Same thing in the right direction when moving right
        if to_right and is_jumping and not is_double_jumping:
            speed_r = 0.5
        elif to_right and is_double_jumping:
            speed_r = 1.0
        return speed_l + speed_r

    def __deceleration(self, to_left: bool, to_right: bool):
        # After releasing the left and right movement keys, the robot doesn't abruptly stop, but decelerates to a halt.
        # This function determines the speed while decelerating (i.e. when neither left nor right is pressed), based on
        # the previous velocity in the horizontal plane.
        speed_l = 0.0
        speed_r = 0.0
        decel_amount = 0.25
        # If previously moving to the left and no key is pressed, decrease speed by 0.25 per frame
        if self.__previous_x_velocity < 0 and not to_left and not to_right:
            speed_l = self.__previous_x_velocity + decel_amount
        # Else if previously moving to the right and no key is pressed, decrease speed by 0.25 per frame
        elif self.__previous_x_velocity > 0 and not to_left and not to_right:
            speed_r = self.__previous_x_velocity - decel_amount
        return speed_l + speed_r

    def __jump(self, is_jumping: bool, is_double_jumping: bool):
        # Setting the gravity value
        gravity = 1
        if is_jumping:
            self.__y -= self.__y_velocity
            # Velocity decreases by the gravity value every frame after initiating a jump
            self.__y_velocity -= gravity
            # Condition to initiate double jump
            if is_double_jumping and not self.__double_jump_is_active:
                # Double jump becomes active, and while this is active the above condition
                # is skipped
                self.__double_jump_is_active = True
                # Velocity is set to double jump height
                self.__y_velocity = self.__height_of_double_jump
            # Condition for when the robot lands, i.e. reaches the initial y coordinate on the
            # bottom of the window.
            if self.__y >= self.__y_initial:
                # Not-so-elegant solution to avoid the robot from falling below the lower
                # window border (because otherwise some more math is needed and this works fine)
                self.__y = self.__y_initial
                # Inactivate the double jump
                self.__double_jump_is_active = False
                # Reset initial y velocity
                self.__y_velocity = self.__height_of_jump
                # Return list of 2 falses to set is_jumping and is_double_jumping in the main
                # program
                return [False, False]
        return [is_jumping, is_double_jumping]

    def __jump_image(self, to_left: bool, to_right: bool, is_jumping: bool):
        # This method returns different images based on jumping (direction)
        if not is_jumping:
            return self.__robot
        elif to_left:
            return self.__robot_jumping_left
        elif to_right:
            return self.__robot_jumping_right
        else:
            # If jumping without a direction, use the jump left image
            return self.__robot_jumping_left

    def get_hitbox(self):
        # Create a hitbox (rectangle object) on the position. Although it uses the
        # robot.png image, this will still work with the jumping images, since
        # they are the same size.
        robot_hitbox = self.__robot.get_rect(topleft=(self.__x, self.__y))
        # Decrease hitbox size by 5% (this simply 'felt' better in game because
        # the robot image has some empty pixels)
        robot_hitbox = robot_hitbox.scale_by(0.95)
        return robot_hitbox

    def reset(self):
        # Reset robot to starting position after game over
        self.__x = self.__window_w / 2
        self.__y = self.__y_initial


class Asteroid:
    speed = 1

    def __init__(self, window: pygame.surface.Surface):
        # The number of points an asteroid is worth. Base value is 1. Randomizer
        # creates larger asteroids occasionally that are worth more points. Needs
        # to be defined before the randomization of asteroid below, since
        # it alters this value sometimes.
        self._points = 1
        # Loading asteroid image
        self._object = self._randomize()
        # Setting window and determining window sizes
        self._window = window
        self._window_w = window.get_width()
        self._window_h = window.get_height()
        # Set initial position of the randomly spawning asteroid
        # Spawns above the upper screen border and on a random horizontal coordinate
        self._x = randint(0, self._window_w - self._object.get_width())
        self._y = -self._object.get_height()
        # Speed in the vertical direction is class speed + random number ranging from
        # -0,5 (50% speed) to 1,0 (200% speed)
        self._y_speed = Asteroid.speed + (randint(-5, 10) / 10)
        # Speed in the horizontal direction with normal distribution with mean 0
        self._x_speed = np.random.normal(0, self._y_speed * 0.08, 1)[0]
        # Rotation angle
        self._rotation_angle = randint(0, 90) / 1000

    @property
    def points(self):
        return self._points

    def _next_coordinates(self):
        # Calculates the next coordinates (very simple in this version, can be expanded upon)
        coordinates = (self._x, self._y)
        self._x += self._x_speed
        self._y += self._y_speed
        return coordinates

    def _randomize(self):
        # This method randomizes the asteroid size, angle and orientation
        asteroid = pygame.image.load("asteroid.png")
        # Pick a random angle for the image
        angle = randint(0, 359)
        asteroid = pygame.transform.rotate(asteroid, angle)
        # The size changes depending on rotation, we pick it up here
        w = asteroid.get_width()
        h = asteroid.get_height()
        # We randomize the scale, being between 20-50% of the original
        scale = randint(2, 5) / 10
        # 10% chance to increase size by 50%, 3% chance to increase size by 100%
        scale_percent = randint(0, 100)
        if scale_percent < 10:
            multiplier = 1.5
            # Asteroid worth 2 points when this multiplier is applied
            self._points = 2
        elif scale_percent < 3:
            multiplier = 2
            # Asteroid worth 3 points when this multiplier is applied
            self._points = 3
        else:
            multiplier = 1
        asteroid = pygame.transform.scale(
            asteroid, (w * scale * multiplier, h * scale * multiplier)
        )
        # Random horizontal/vertical flips
        asteroid = pygame.transform.flip(
            asteroid, bool(randint(0, 1)), bool(randint(0, 1))
        )
        # Return the randomized image
        return asteroid

    def _get_hitbox(self):
        # Create the hitbox of the asteroid
        object_hitbox = self._object.get_rect(topleft=(self._x, self._y))
        # Decrease the scale of the hitbox by 10% (collision corresponds
        # better to the actual image displayed this way)
        object_hitbox = object_hitbox.scale_by(0.90)
        return object_hitbox

    def on_screen(self):
        # Returns False when the asteroid is below the lower border (signal to delete
        # in the main game)
        if self._y > self._window_h + 1:
            return False
        return True

    def collision(self, robot: Robot):
        # Get the robot hitbox
        robot_hitbox = robot.get_hitbox()
        # Get the asteroid hitbox
        object_hitbox = self._get_hitbox()
        # Moves the asteroid 1000 pixels down (i.e.  off screen), where the main
        # program will delete it from the asteroid list
        if robot_hitbox.colliderect(object_hitbox):
            self._y += 1000
            # Returns a tuple of a bool (True means there has been collision) and
            # the number of points an asteroid of given size is worth
            return (True, self._points)
        # Condition not met, so no collision
        return False

    def fall(self):
        self._window.blit(self._object, self._next_coordinates())


class Heart(Asteroid):
    # This class can create Heart objects, which are hearts falling from the sky that
    # will increase the player's number of lives. It behaves like the asteroid class,
    # so it has been made as a subclass of that.
    def __init__(self, window: pygame.surface.Surface):
        super().__init__(window)
        # Image not imported from superclass because it's not randomized here
        self._object = pygame.image.load("heart.png")
        # Speed is always the same, unlike for asteroids, and they always fall
        # straight down and don't rotate
        self._y_speed = Asteroid.speed
        self._x_speed = 0
        self._rotation_angle = 0


class FileHandler:
    def __init__(self, file_name):
        self.__file_name = file_name

    def load_file(self):
        high_score = []
        with open(self.__file_name) as f:
            for line in f:
                high_score.append(int(line.strip()))
        return high_score[0]

    def save_file(self, high_score: int):
        with open(self.__file_name, "w") as f:
            f.write(f"{high_score}")


class AsteroidGame:
    def __init__(self):
        # Game name
        self.__name = "Asteroids"
        # Setting up the window
        self.__window_w = 640
        self.__window_h = 480
        self.__window = pygame.display.set_mode((self.__window_w, self.__window_h))
        # Background color is black
        self.__bg_color = (0, 0, 0)
        # Settin up the playable robot
        self.__robot = Robot(self.__window)
        # Default controls
        self.__controls = {
            "move_left": pygame.K_a,
            "move_right": pygame.K_d,
            "run": pygame.K_w,
            "jump": pygame.K_SPACE,
            "pause": pygame.K_ESCAPE,
        }
        # Setting up the game clock and fps
        self.__clock = pygame.time.Clock()
        self.__fps = 60

        self.__filehandler = FileHandler("highscore.txt")

    def __register_inputs(self, inputs: dict):
        # This method changes values in the 'inputs' dictionary based on
        # registered keystrokes that correspond with keys specified
        # in the 'controls' dictionary.
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == self.__controls["move_left"]:
                    inputs["to_left"] = True
                if event.key == self.__controls["move_right"]:
                    inputs["to_right"] = True
                if event.key == self.__controls["run"]:
                    inputs["is_running"] = True
                if event.key == self.__controls["jump"]:
                    if not inputs["is_jumping"]:
                        inputs["is_jumping"] = True
                    elif inputs["is_jumping"] and not inputs["is_double_jumping"]:
                        inputs["is_double_jumping"] = True
                if event.key == self.__controls["pause"]:
                    inputs["pause_status_change"] = True

            if event.type == pygame.KEYUP:
                if event.key == self.__controls["move_left"]:
                    inputs["to_left"] = False
                if event.key == self.__controls["move_right"]:
                    inputs["to_right"] = False
                if event.key == self.__controls["run"]:
                    inputs["is_running"] = False

            if event.type == pygame.QUIT:
                exit()

    def __ingame_text(
        self,
        score: int,
        high_score: int,
        lives: int,
        text_font1: pygame.font.Font,
        text_font2: pygame.font.Font,
    ):
        # Colors (red and green)
        score_color = (255, 0, 0)
        lives_color = (50, 205, 50)
        # Text objects for score and lives
        score_text = text_font1.render(f"Score: {score}", True, score_color)
        high_score_text = text_font2.render(
            f"(High score: {high_score})", True, score_color
        )
        lives_text = text_font1.render(f"+", True, score_color)
        # Blit
        self.__window.blit(score_text, (500, 20))
        self.__window.blit(high_score_text, (500, 45))
        # Display lives as hearts
        heart_object = pygame.image.load("heart.png")
        for i in range(lives):
            if i > 10:
                self.__window.blit(
                    lives_text, (30 + heart_object.get_width() * 11 + 3, 14)
                )
            else:
                self.__window.blit(
                    heart_object, (30 + heart_object.get_width() * i, 20)
                )

        # self.__window.blit(lives_text, (500, 70))

    def __pause_handler(self, state: int, inputs: dict):
        # Do nothing if game over (since the pause key will be used for
        # another purpose in this state)
        if state == -1:
            return state
        # Return the input game state if pause key hasn't been pressed.
        # If the pause key is pressed in the previous frame, change it
        # to 'unpressed' in this frame and change the game state accordingly
        # (i.e. if game is paused, unpause, and vice versa).
        if not inputs["pause_status_change"]:
            return state
        else:
            inputs["pause_status_change"] = False
            return 1 if state == 0 else 0

    def __pause_menu(self, text_font: pygame.font.Font):
        # Set text color
        text_color = (255, 255, 255)
        # Create text object
        text = text_font.render(
            "Game paused. Press 'Esc' to continue...", True, text_color
        )
        # Create rectangle for text object so it can be centered easily
        text_rect = text.get_rect(center=(self.__window_w / 2, self.__window_h / 2))
        # Create on display
        self.__window.blit(text, text_rect)

    def __game_over_handler(
        self, lives: int, score: int, high_score: int, state: int, inputs: dict
    ):
        # Return value is the new game state.
        if lives <= 0:
            # If the player has 0 lives and the game isn't in game-over state,
            # this state will be set.
            if state != -1:
                return -1
            # If the game is in game-over state, check if the player presses the
            # 'Esc' key. Execute a new game.
            else:
                if inputs["pause_status_change"]:
                    if score > high_score:
                        self.__filehandler.save_file(score)
                    inputs["pause_status_change"] = False  # TODO might not be necessary
                    self.execute()
        return state

    def __game_over_menu(
        self, text_font: pygame.font.Font, header_font: pygame.font.Font
    ):
        # Set text color
        text_color = (255, 255, 255)
        # Create header and text object
        header = header_font.render("GAME OVER", True, text_color)
        text = text_font.render("Press 'Esc' to restart", True, text_color)
        # Create rectangles for easy centering
        header_rect = header.get_rect(center=(self.__window_w / 2, 220))
        text_rect = text.get_rect(center=(self.__window_w / 2, 270))
        # Create on display
        self.__window.blit(header, header_rect)
        self.__window.blit(text, text_rect)

    def __spawner(self, score: int, asteroids: list, hearts: dict):
        # ASTEROIDS
        # Base spawn chance (out of 1000), increases gradually with points scored
        base_spawn_chance = 8
        spawn_chance = base_spawn_chance + (score / 5)
        if randint(0, 1000) < spawn_chance:
            asteroids.append([Asteroid(self.__window), False])

        # HEARTS
        # Spawn every 10 points scored + variable factor dependent on score
        # The higher the score, the less hearts spawn. At 1000 score, no more
        # hearts spawn
        heart_spawn_chance = 1010 - score
        if score % 10 == 0 and score != 0 and score not in hearts.keys():
            if randint(0, 1000) < heart_spawn_chance:
                hearts[score] = [Heart(self.__window), False]

    def __updated_score(self, score: int, asteroids: list):
        # See description in updated_lives(). Checks the bool in index [1] of
        # an entry in the list. If True, then score increases.
        for asteroid in asteroids:
            if asteroid[1]:
                score += asteroid[0].points
        return score

    def __updated_lives(self, lives: int, asteroids: list, hearts: dict):
        # The items in the asteroids list are 2-item lists. The first item in this
        # sublist contains the asteroid object, the second contains a bool stating
        # whether or not the object has collided with the player in the previous
        # frame.
        # When the asteroid has gone offscreen, it can either be because the player
        # collided with it (no loss of a life) or because it fell through the lower
        # border of the screen (loss of a life)
        for asteroid in asteroids:
            if not asteroid[0].on_screen() and not asteroid[1]:
                lives -= 1
        # When hearts collide with the robot, the number of lives increases by 1.
        # Values in the hearts dict have the followin structure:
        # hearts[spawn_time] = [Heart(), bool(collision with player in previous frame?)]
        for heart in hearts.values():
            if heart[1]:
                lives += 1
        return lives

    def __delete_offscreen_objects(self, asteroids: list, hearts: dict):
        # Remove offscreen asteroids from list
        asteroids = [asteroid for asteroid in asteroids if asteroid[0].on_screen()]
        # Remove offscreen hearts from dict
        for k in list(hearts.keys()):
            if not hearts[k][0].on_screen():
                del hearts[k]
        return asteroids, hearts

    def __collision_check(self, asteroids: list, hearts: dict):
        # ASTEROID COLLISION CHECK
        for asteroid in asteroids:
            # Let asteroid fall
            asteroid[0].fall()
            # Check for collision, adjust variable on index[1] accordingly
            # (default [1] = False, after collision [1] = True)
            if asteroid[0].collision(self.__robot):
                asteroid[1] = True

        # HEART COLLISION CHECK
        for heart in hearts.values():
            # Let heart fall
            heart[0].fall()
            # Check for collision, see above
            if heart[0].collision(self.__robot):
                heart[1] = True

    def execute(self):
        # Start pygame
        pygame.init()
        self.__robot.reset()
        # Display the game name in the caption
        pygame.display.set_caption(self.__name)
        # Set the different fonts for ingame and the game over text
        game_font1 = pygame.font.SysFont("Arial", 20)
        game_font2 = pygame.font.SysFont("Arial", 40)
        game_font3 = pygame.font.SysFont("Arial", 15)
        # Game inputs. Set to false at the start of every game.
        game_inputs = {
            "to_left": False,
            "to_right": False,
            "is_running": False,
            "is_jumping": False,
            "is_double_jumping": False,
            "pause_status_change": False,
        }
        # Initial score and lives of the player.
        player_score = 0
        player_lives = 3
        # State of the game. Starting state = playing
        paused, playing, game_over = 0, 1, -1
        game_state = playing
        # Asteroids (list) and hearts (dict) currently spawned. A dict
        # for hearts is used to link the heart object to a score. Hearts
        # spawn when a certain score is reached. We don't want hearts to
        # keep spawning at this score. The score is used as key in the
        # dictionary, so it can be checked to avoid double spawns.
        spawned_asteroids = []
        spawned_hearts = {}
        # Loading highscore from file
        try:
            high_score = self.__filehandler.load_file()
        except FileNotFoundError:
            high_score = 0

        while True:
            # Register the inputs
            self.__register_inputs(game_inputs)
            # Check pause and game-over state conditions, and change game state accordingly
            game_state = self.__pause_handler(game_state, game_inputs)
            game_state = self.__game_over_handler(
                player_lives, player_score, high_score, game_state, game_inputs
            )
            # Fill the window with the set background color
            self.__window.fill(self.__bg_color)

            # PLAYING / PAUSED / GAME OVER GAME STATES
            if game_state == playing:
                # Robot registers controls
                self.__robot.play(game_inputs)
                # Spawner of hearts and asteroids
                self.__spawner(player_score, spawned_asteroids, spawned_hearts)
                # New value for score and lives is calculated
                player_score = self.__updated_score(player_score, spawned_asteroids)
                player_lives = self.__updated_lives(
                    player_lives, spawned_asteroids, spawned_hearts
                )
                # Delete spawned after score/lives update
                spawned_asteroids, spawned_hearts = self.__delete_offscreen_objects(
                    spawned_asteroids, spawned_hearts
                )
                # Collision checker
                self.__collision_check(spawned_asteroids, spawned_hearts)
                # Create game text
                self.__ingame_text(
                    player_score, high_score, player_lives, game_font1, game_font3
                )
            elif game_state == paused:
                self.__pause_menu(game_font1)
            elif game_state == game_over:
                self.__game_over_menu(game_font1, game_font2)

            # Frame generation
            pygame.display.flip()
            self.__clock.tick(self.__fps)


def main():
    AsteroidGame().execute()


if __name__ == "__main__":
    main()
