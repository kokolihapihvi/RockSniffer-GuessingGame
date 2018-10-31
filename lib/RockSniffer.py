import json

class Sniffer(object):
    def __init__(self, ip, port, getreqfunc, putreqfunc, logfunc):
        super(Sniffer, self).__init__()

        self.LastPoll = None
        self.URL = "http://{0}:{1}/".format(ip,port)
        self.StorageURL = "http://{0}:{1}/storage/".format(ip,port)
        self.GetRequest = getreqfunc
        self.PutRequest = putreqfunc
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

    def GetStorage(self, addonid):
    	return SnifferStorage(addonid, self)

class SnifferState():
    NONE = 0
    IN_MENUS = 1
    SONG_SELECTED = 2
    SONG_STARTING = 3
    SONG_PLAYING = 4
    SONG_ENDING = 5

""" Sniffer Storage """
class SnifferStorage(object):
	def __init__(self, addonid, sniffer):
		super(SnifferStorage, self).__init__()

		self.Sniffer = sniffer
		self.StorageURL = "{0}{1}/".format(self.Sniffer.StorageURL, addonid)

	def Store(self, key, value):
		if type(value) is not dict:
			raise ValueError("Value must be dict")

		self.Sniffer.PutRequest("{0}{1}".format(self.StorageURL, key), {}, value, True)

	def Get(self, key):
		return json.loads(self.Sniffer.GetRequest("{0}{1}".format(self.StorageURL, key)))