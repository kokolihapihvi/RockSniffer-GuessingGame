import time

class GuessingGame(object):
    def __init__(self, log, storage):
        super(GuessingGame, self).__init__()

        self.Log = log
        self.Storage = storage

        self.Running = False
        self.Completed = False
        self.Guesses = list()
        self.StartTime = time.time()

        self.Storage.Store("guesses", {"Guesses": self.Guesses})

    """Start the guessing game"""
    def StartGame(self):
        self.Running = True
        self.Log("Starting game")

    """Close for new guesses"""
    def CloseGame(self):
        self.Running = False
        self.Log("Game closed")

    """End the guessing game"""
    def EndGame(self, accuracy):
        self.Completed = True

        if self.Running:
            return

        self.Log("Ending with {0}% accuracy".format(accuracy))

        if len(self.Guesses) == 0:
            return list()

        # Sort by distance
        self.Guesses.sort(key = lambda guess: abs(guess["guess"] - accuracy))

        # Calculate best distance
        BestDist = abs(self.Guesses[0]["guess"] - accuracy)

        Winners = list()

        # Build a list of winners
        for idx, member in enumerate(self.Guesses):
            # Calculate distance
            dist = abs(member["guess"] - accuracy)

            # Add distance to the object
            self.Guesses[idx]["distance"] = dist

            if dist == BestDist:
                Winners.append(member)

            self.Log("{}".format(str(member)))

        return Winners

    """Add new guess to the guesses"""
    def AddGuess(self, name, guess):
        if not self.Running:
            return False

        if filter(lambda x: x["name"].lower() == name.lower(), self.Guesses):
            return False

        self.Guesses.append({"name": name, "guess": guess})

        self.Log("Added guess {0}: {1}".format(name, guess))

        self.Storage.Store("guesses", {"Guesses": self.Guesses})

        return True
