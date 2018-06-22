import json

class Sniffer(object):
    def __init__(self, ip, port, reqfunc, logfunc):
        super(Sniffer, self).__init__()

        self.LastPoll = None
        self.URL = "http://{0}:{1}/".format(ip,port)
        self.GetRequest = reqfunc
        self.Log = logfunc

    def Poll(self):
        try:
            resp = self.GetRequest(self.URL, {})
            self.LastPoll = json.loads(json.loads(resp)["response"])
            
            return True
        except Exception as e:
            return False

    def GetSongName(self):
        if self.LastPoll is None:
            return "Unknown"

        return self.LastPoll["songDetails"]["songName"]

    def GetArtistName(self):
        if self.LastPoll is None:
            return "Unknown"

        return self.LastPoll["songDetails"]["artistName"]

    def GetAccuracy(self):
        if self.LastPoll is None:
            return 0.0

        # Calculate total notes
        totalNotes = self.LastPoll["memoryReadout"]["totalNotesHit"] + self.LastPoll["memoryReadout"]["totalNotesMissed"]

        # Avoid dividing by 0
        if totalNotes == 0:
            return 0.0

        # Calculate accuracy
        accuracy = float(self.LastPoll["memoryReadout"]["totalNotesHit"]) / float(totalNotes)

        # Translate from fraction to percentage
        accuracy *= 100.0

        # Round to 2 decimal places
        accuracy = float(str(round(accuracy, 2)))

        return accuracy

    def GetState(self):
        if self.LastPoll is None:
            return 0

        return self.LastPoll["currentState"]

    def Unload(self):
        return

class SnifferState():
    NONE = 0
    IN_MENUS = 1
    SONG_SELECTED = 2
    SONG_STARTING = 3
    SONG_PLAYING = 4
    SONG_ENDING = 5