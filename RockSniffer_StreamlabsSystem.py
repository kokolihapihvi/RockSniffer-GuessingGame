#---------------------------------------
# Import Libraries
#---------------------------------------
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))

from RockSniffer_Settings import SnifferSettings
from RockSniffer import Sniffer, SnifferState
from RockSniffer_GuessingGame import GuessingGame

#---------------------------------------
# [Required] Script Information
#---------------------------------------
ScriptName  = "RockSniffer Guessing Game"
Website     = "https://github.com/kokolihapihvi/RockSniffer-GuessingGame"
Description = "RockSniffer integration, now with 20% more sniff"
Creator     = "Kokolihapihvi"
Version     = "0.0.12"

#---------------------------------------
# Set Variables
#---------------------------------------
Settings          = None
SettingsFile      = ""
m_Sniffer         = None
m_GuessingGame    = None
LastPollTime      = 0
SongCounter       = 0
SongCounterLock   = False
WinnerFile        = os.path.join(os.path.dirname(__file__), "gg_winner.txt")

#---------------------------------------
# [Required] Intialize Data (Only called on Load)
#---------------------------------------
def Init():
    global HTTPConnection
    global Settings
    global SettingsFile
    global m_Sniffer

    # Load settings
    SettingsFile = os.path.join(os.path.dirname(__file__), "SnifferConfig.json")
    Settings = SnifferSettings(SettingsFile)

    # Ready the sniffer
    m_Sniffer = Sniffer(Settings.sniffer_ip, Settings.sniffer_port, Parent.GetRequest, lambda x: Parent.Log("Sniffer", str(x)))

    return

#---------------------------------------
# [Optional] Replace parameters
#---------------------------------------
def Parse(parseString, user, target, message):
    if "$sniffer_song" in parseString:
        return parseString.replace("$sniffer_song", m_Sniffer.GetSongName())

    if "$sniffer_artist" in parseString:
        return parseString.replace("$sniffer_artist", m_Sniffer.GetArtistName())

    if "$sniffer_accuracy" in parseString:
        return parseString.replace("$sniffer_accuracy", "{0:.2f}%".format(m_Sniffer.GetAccuracy()))

    return parseString

#---------------------------------------
# [Required] Execute Data / Process Messages
#---------------------------------------
def Execute(data):
    global m_GuessingGame
    global m_Sniffer
    global Settings

    if data.IsChatMessage() and data.IsFromTwitch():
        if data.GetParam(0).lower() == Settings.gg_start_command:
            if m_GuessingGame is None or m_GuessingGame.Completed:
                if not Parent.HasPermission(data.User, "moderator", ""):
                    return
                StartGame()
                return

            Parent.SendTwitchMessage("Guessing game already running")
        elif data.GetParam(0).lower() == Settings.gg_end_command:
            if m_GuessingGame is None or m_GuessingGame.Completed:
                return

            if not Parent.HasPermission(data.User, "moderator", ""):
                return

            try:
                Guess = max(0.0, min(100.0, float(data.GetParam(1))))
            except Exception as e:
                Guess = m_Sniffer.GetAccuracy()

            EndGame(Guess)
        elif data.GetParam(0).lower() == Settings.gg_guess_command:
            if m_GuessingGame is None or m_GuessingGame.Completed:
                return

            if not Parent.RemovePoints(data.User, Settings.gg_guess_command_price):
                Parent.SendTwitchMessage("@{0} You can't afford that".format(data.User))
                return

            try:
                Guess = max(0.0, min(100.0, float(data.GetParam(1))))
            except Exception as e:
                return

            if Guess is None:
                return

            if m_GuessingGame.AddGuess(data.User, Guess):
                Parent.SendTwitchMessage("@{0} guesses {1:.2f}%".format(data.User, Guess))
        elif data.GetParam(0).lower() == Settings.gg_cancel_command:
            if m_GuessingGame is None or m_GuessingGame.Completed:
                return

            if not Parent.HasPermission(data.User, "moderator", ""):
                return

            m_GuessingGame = None

            Parent.SendTwitchMessage("Guessing game has been cancelled")

        elif data.GetParam(0).lower() == Settings.gg_autostart_command:
            if not Parent.HasPermission(data.User, "moderator", ""):
                return
            Settings.gg_autostart = not Settings.gg_autostart
            Parent.SendTwitchMessage("Guessing game autostart has been set to {0}".format(Settings.gg_autostart))

        elif data.GetParam(0).lower() == Settings.gg_autoend_command:
            if not Parent.HasPermission(data.User, "moderator", ""):
                return
            Settings.gg_autoend = not Settings.gg_autoend
            Parent.SendTwitchMessage("Guessing game autoend has been set to {0}".format(Settings.gg_autoend))

    return

#---------------------------------------
# [Required] Tick Function
#---------------------------------------
def Tick():
    global LastPollTime
    global Settings
    global m_Sniffer
    global SongCounter
    global SongCounterLock

    # Poll every sniffer_pollrate seconds
    if time.time() > LastPollTime + Settings.sniffer_pollrate:
        LastPollTime = time.time()

        if m_Sniffer.Poll() == False:
            Parent.Log(ScriptName, "Poll failed, check that RockSniffer is running and that configuration is correct")

    # Check guessing game state
    if not m_GuessingGame is None and m_GuessingGame.Running:
        if time.time() > m_GuessingGame.StartTime + Settings.gg_closedelay:
            CloseGame()

    # Automatically start guessing game
    if Settings.gg_autostart:
        if m_GuessingGame is None or m_GuessingGame.Completed:
            # If state is SONG_STARTING or SONG_PLAYING
            if m_Sniffer.GetState() == SnifferState.SONG_PLAYING or m_Sniffer.GetState() == SnifferState.SONG_STARTING:
                if not SongCounterLock:
                    SongCounterLock = True
                    SongCounter += 1
                    Parent.Log(ScriptName, "{0}/{1}".format(SongCounter, Settings.gg_autostart_songs))

                if SongCounter >= Settings.gg_autostart_songs:
                    SongCounter = 0
                    StartGame()
            else:
                SongCounterLock = False
        else:
            SongCounterLock = False


    # Automatically end guessing game
    if Settings.gg_autoend:
        # If there is a guessing game running
        if not m_GuessingGame is None and not m_GuessingGame.Completed:
            # If state is IN_MENUS or SONG_ENDING
            if m_Sniffer.GetState() == SnifferState.IN_MENUS or m_Sniffer.GetState() == SnifferState.SONG_ENDING:
                EndGame(m_Sniffer.GetAccuracy())

    return
#---------------------------
#   [Optional] Reload Settings (Called when a user clicks the Save Settings button in the Chatbot UI)
#---------------------------
def ReloadSettings(jsonData):
    global Settings

    # Execute json reloading here
    Settings.Reload(jsonData)

    return

#---------------------------
# [Optional] Unload (Called when a user reloads their scripts or closes the bot / cleanup stuff)
#---------------------------
def Unload():
    global m_Sniffer

    m_Sniffer.Unload()

    return


def StartGame():
    global m_GuessingGame
    global Settings

    m_GuessingGame = GuessingGame(lambda x: Parent.Log("GG", str(x)))
    m_GuessingGame.StartGame()
    Parent.SendTwitchMessage("Started guessing game, you have {0} seconds to !guess the accuracy".format(Settings.gg_closedelay))

    return


def CloseGame():
    global m_GuessingGame

    m_GuessingGame.CloseGame()
    Parent.SendTwitchMessage("The guessing game is now closed, no new guesses allowed")

    return

def EndGame(accuracy):
    global m_GuessingGame
    global Settings

    m_GuessingGame.CloseGame()
    Winners = m_GuessingGame.EndGame(accuracy)

    # Delay annoucing results to line up with end of song on stream
    time.sleep(Settings.gg_videosync_delay)

    if len(Winners) == 0:
        Parent.SendTwitchMessage("The guessing game has ended. Nobody guessed, nobody won")
        return

    Winner_Names = list(map(lambda x: x["name"], Winners))

    ##
    win_rwd   = Settings.gg_reward
    win_msg   = "had the closest guess of"
    win_guess = m_GuessingGame.BestGuess[0][1]
    win_dist  = accuracy - win_guess

    # Check if jackpot was enabled and hit
    if Settings.gg_jackpot:
        if Winners[0]["distance"] <= Settings.gg_jackpot_threshold:
            win_rwd    = Settings.gg_jackpot_reward
            win_msg  = "hit the JACKPOT with a guess of"

    msg = "The guessing game has ended, accuracy is {0:.2f}%. {1} {2} {3} ({4:.2f} away) and wins {5} {6}!!".format(accuracy, my_join(Winner_Names), win_msg, win_guess, win_dist, win_rwd, Parent.GetCurrencyName())

    Parent.SendTwitchMessage(msg)

    if Settings.gg_write_winners_file:
        with open(WinnerFile, "w") as f:
            f.write(", ".join(Winner_Names))

    for idx, winner in enumerate(Winners):
        Parent.AddPoints(winner["name"], win_rwd)

    return


def my_join(lst):
    if not lst:
        return ""
    elif len(lst) == 1:
        return str(lst[0])

    return "{} and {}".format(", ".join(lst[:-1]), lst[-1])
