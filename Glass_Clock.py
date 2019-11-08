# Glass Clock, Craig Rettew, 2019
# Alexa Gadget Shenanigans

# Copyright 2019 Amazon.com, Inc. or its affiliates.  All Rights Reserved.
# These materials are licensed under the Amazon Software License in connection with the Alexa Gadgets Program.
# The Agreement is available at https://aws.amazon.com/asl/.
# See the Agreement for the specific terms and conditions of the Agreement.
# Capitalized terms not defined in this file have the meanings given to them in the Agreement.
#

# Check logs if shit goes down
# cd logs
# cat cronlog

import logging
import sys
import threading
import time
import math

import datetime
import board
import neopixel

import dateutil.parser
from agt import AlexaGadget

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

# Pin used to talk pixel lingo
pixel_pin = board.D18

# The number of NeoPixels
num_pixels = 134

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=1, auto_write=False, pixel_order=ORDER)

# Each Segement of each digit defined in a dictionary
#0x:xx:xx
digit_1 = {
    1:(0, 1, 2),
    2:(3, 4, 5),
    3:(6, 7, 8),
    4:(9, 10, 11),
    5:(12, 13, 14),
    6:(15, 16, 17),
    7:(18, 19, 20)
}
#x0:xx:xx
digit_2 = {
    1:(21, 22, 23),
    2:(24, 25, 26),
    3:(27, 28, 29),
    4:(30, 31, 32),
    5:(33, 34, 35),
    6:(36, 37, 38),
    7:(39, 40, 41)
}


colon_1 = [42,43,44,45]

#xx:0x:xx
digit_3 = {
    1:(46,47,48),
    2:(49,50,51),
    3:(52,53,54),
    4:(55,56,57),
    5:(58,59,60),
    6:(61,62,63),
    7:(64,65,66)
}

#xx:x0:xx
digit_4 = {
    1:(67,68,69),
    2:(70,71,72),
    3:(73,74,75),
    4:(76,77,78),
    5:(79,80,81),
    6:(82,83,84),
    7:(85,86,87)
}

colon_2 = [88, 89, 90, 91]

#xx:xx:0x
digit_5 = {
    1:(92,93,94),
    2:(95,96,97),
    3:(98,99,100),
    4:(101,102,103),
    5:(104,105,106),
    6:(107,108,109),
    7:(110,111,112)
}

#xx:xx:x0
digit_6 = {
    1:(113,114,115),
    2:(116,117,118),
    3:(119,120,121),
    4:(122,123,124),
    5:(125,126,127),
    6:(128,129,130),
    7:(131,132,133)
}

# Defines which segments to light up/not light up for each number 0-9
nums = {
    0:[[1,2,3,5,6,7],[4]],
    1:[[3,7],[1,2,4,5,6]],
    2:[[2,3,4,5,6],[1,7]],
    3:[[2,3,4,6,7],[1,5]],
    4:[[1,3,4,7],[2,5,6]],
    5:[[1,2,4,6,7],[3,5]],
    6:[[1,2,4,5,6,7],[3]],
    7:[[2,3,7],[1,4,5,6]],
    8:[[1,2,3,4,5,6,7],[]],
    9:[[1,2,3,4,6,7],[5]]
}

# Color defintions for days in the month gradient
days = {
    1:(0,0,255),#blue
    2:(0,33,255),
    3:(0,68,255),
    4:(0,101,255),
    5:(0,136,255),
    6:(0,169,255),
    7:(0,203,255),
    8:(0,238,255),
    9:(0,255,237),
    10:(0,255,203),
    11:(0,255,169),
    12:(0,255,136),
    13:(0,255,101),
    14:(0,255,67),
    15:(0,255,33),
    16:(0,255,0),
    17:(34,255,0),
    18:(68,255,0),
    19:(101,255,0),
    20:(136,255,0),
    21:(170,255,0),
    22:(204,255,0),
    23:(238,255,0),
    24:(255,237,0),
    25:(255,204,0),
    26:(255,170,0),
    27:(255,136,0),
    28:(255,102,0),
    29:(255,67,0),
    30:(255,33,0),
    31:(255,0,0)#red
}

# Defined colors
RED = (255,0,0)
GREEN = (0,255,0)
BLUE = (0,0,255)
PURPLE = (255,0,255)
ORANGE = (255,67,0)
WHITE = (255,255,255)


# Setting the color of the colons
def colonSet(color):

    for num in range(0,4):
        pixels[colon_1[num]] = color
        pixels[colon_2[num]] = color
    pixels.show()

def wheel(pos):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        r = g = b = 0
    elif pos < 85:
        r = int(pos * 3)
        g = int(255 - pos*3)
        b = 0
    elif pos < 170:
        pos -= 85
        r = int(255 - pos*3)
        g = 0
        b = int(pos*3)
    else:
        pos -= 170
        r = 0
        g = int(pos*3)
        b = int(255 - pos*3)
    return (r, g, b) if ORDER == neopixel.RGB or ORDER == neopixel.GRB else (r, g, b, 0)


def rainbow_cycle(wait):
    for j in range(255):
        for i in range(num_pixels):
            pixel_index = (i * 256 // num_pixels) + j
            pixels[i] = wheel(pixel_index & 255)
        pixels.show()
        time.sleep(wait)

# Illuminate the digits for given number and color
def display_digits(digits, color):

    # Parse out individual digits
    hrsLeft = digits[0]
    hrsRight = digits[1]

    minsLeft = digits[3]
    minsRight = digits[4]

    secsLeft = digits[6]
    secsRight = digits[7]

    #print("Timer Fomatted: " + str(hrsLeft) + str(hrsRight) + ":" + str(minsLeft) + str(minsRight) + ":" + str(secsLeft) + str(secsRight))
    
    ###############Real Digits################
    # Hours digits loops
    for onLoop in range(0,len(nums[int(hrsLeft)][0])):
        for pix in range(0,3):
            pixels[digit_1[nums[int(hrsLeft)][0][onLoop]][pix]] = color
            for offLoop in range(0,len(nums[int(hrsLeft)][1])):
                pixels[digit_1[nums[int(hrsLeft)][1][offLoop]][pix]] = (0,0,0)

    for onLoop in range(0,len(nums[int(hrsRight)][0])):
        for pix in range(0,3):
            pixels[digit_2[nums[int(hrsRight)][0][onLoop]][pix]] = color
            for offLoop in range(0,len(nums[int(hrsRight)][1])):
                pixels[digit_2[nums[int(hrsRight)][1][offLoop]][pix]] = (0,0,0)

    # Mins digits loops
    for onLoop in range(0,len(nums[int(minsLeft)][0])):
        for pix in range(0,3):
            pixels[digit_3[nums[int(minsLeft)][0][onLoop]][pix]] = color
            for offLoop in range(0,len(nums[int(minsLeft)][1])):
                pixels[digit_3[nums[int(minsLeft)][1][offLoop]][pix]] = (0,0,0)

    for onLoop in range(0,len(nums[int(minsRight)][0])):
        for pix in range(0,3):
            pixels[digit_4[nums[int(minsRight)][0][onLoop]][pix]] = color
            for offLoop in range(0,len(nums[int(minsRight)][1])):
                pixels[digit_4[nums[int(minsRight)][1][offLoop]][pix]] = (0,0,0)

    # Sec digits loops
    for onLoop in range(0,len(nums[int(secsLeft)][0])):
        for pix in range(0,3):
            pixels[digit_5[nums[int(secsLeft)][0][onLoop]][pix]] = color
            for offLoop in range(0,len(nums[int(secsLeft)][1])):
                pixels[digit_5[nums[int(secsLeft)][1][offLoop]][pix]] = (0,0,0)

    for onLoop in range(0,len(nums[int(secsRight)][0])):
        for pix in range(0,3):
            pixels[digit_6[nums[int(secsRight)][0][onLoop]][pix]] = color
            for offLoop in range(0,len(nums[int(secsRight)][1])):
                pixels[digit_6[nums[int(secsRight)][1][offLoop]][pix]] = (0,0,0)
    ################
    pixels.show()


# Alexa Gadget code
class TimerGadget(AlexaGadget):
    """
    An Alexa Gadget that reacts to a single timer set on an Echo device.

    A servo rotates a disc to indicate the remaining duration of the timer,
    when the timer expires, and when a timer is canceled.

    Threading is used to prevent blocking the main thread when the timer is
    counting down.
    """

    def __init__(self):
        super().__init__()
        self.timer_thread = None
        self.clock_thread = None
        self.timer_token = None
        self.timer_end_time = None

        # Start Clock Thread
        self.clock_thread = threading.Thread(target=self._run_clock)
        self.clock_thread.start()

    def on_alerts_setalert(self, directive):
        """
        Handles Alerts.SetAlert directive sent from Echo Device
        """
        # check that this is a timer. if it is something else (alarm, reminder), just ignore
        if directive.payload.type != 'TIMER':
            logger.info("Received SetAlert directive but type != TIMER. Ignorning")
            return

        # parse the scheduledTime in the directive. if is already expired, ignore
        t = dateutil.parser.parse(directive.payload.scheduledTime).timestamp()
        if t <= 0:
            logger.info("Received SetAlert directive but scheduledTime has already passed. Ignoring")
            return

        # check if this is an update to an alrady running timer (e.g. users asks alexa to add 30s)
        # if it is, just adjust the end time
        if self.timer_token == directive.payload.token:
            logger.info("Received SetAlert directive to update to currently running timer. Adjusting")
            self.timer_end_time = t
            return

        # check if another timer is already running. if it is, just ignore this one
        if self.timer_thread is not None and self.timer_thread.isAlive():
            logger.info("Received SetAlert directive but another timer is already running. Ignoring")
            return

        # start a thread to rotate the servo
        logger.info("Received SetAlert directive. Starting a timer. " + str(int(t - time.time())) + " seconds left..")
        self.timer_end_time = t
        self.timer_token = directive.payload.token

        # run timer in it's own thread to prevent blocking future directives during count down
        self.timer_thread = threading.Thread(target=self._run_timer)
        self.timer_thread.start()

    def on_alerts_deletealert(self, directive):
        """
        Handles Alerts.DeleteAlert directive sent from Echo Device
        """
        # check if this is for the currently running timer. if not, just ignore
        if self.timer_token != directive.payload.token:
            logger.info("Received DeleteAlert directive but not for the currently active timer. Ignoring")
            return

        # delete the timer, and stop the currently running timer thread
        logger.info("Received DeleteAlert directive. Cancelling the timer")
        self.timer_token = None

        pixels.fill(0,0,0)
        pixels.show()

    def _run_timer(self):
        """
        Runs a timer
        """
        colonSet(WHITE)
        # check every 500ms
        start_time = time.time()
        time_remaining = self.timer_end_time - start_time
        while self.timer_token and time_remaining > 0:
            logger.info("Received SetAlert directive. Starting a timer. " + str(time_remaining) + " seconds left..")
            time_total = self.timer_end_time - start_time
            time_remaining = max(0, self.timer_end_time - time.time())

            # Set to Red when timer is at 5
            if time_remaining <= 5:
                color = RED
            # Set to Ornage when timer is at 10
            elif time_remaining <= 10:
                color = ORANGE
            # Else, Purple
            else:
                color = PURPLE

            # Format the timer digits for display_digits() to understand
            timer = time.strftime("%H:%M:%S", time.gmtime(time_remaining))

            # Display the digits
            display_digits(timer, color)
            time.sleep(0.5)

        # Run rainbow cycle when timer is done
        rainbow_cycle(0.001)
        # Set colons back to Purple
        colonSet(PURPLE)

    # Run the clock
    def _run_clock(self):        

        # Set colons to Purple
        colonSet(PURPLE)        
        # Run the clock unless a timer is set on Alexa
        while True:
            if not self.timer_token:
                # Get dat time
                now = datetime.datetime.now()
                # Get the day for color formatting
                day = now.strftime("%-d")
                # Format the timer digits for display_digits() to understand
                clock = time.strftime("%I:%M:%S")

                # Display the digits with the correct day color
                display_digits(clock, days[int(day)])

                time.sleep(0.25)

if __name__ == '__main__':
    try:
        TimerGadget().main()
    finally:
        if KeyboardInterrupt:
            pixels.fill(0,0,0)
            pixels.show()
