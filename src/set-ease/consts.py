from anki.utils import isMac, isWin, pointVersion

ANKI_VERSION = pointVersion()
PLATFORM = "win" if isWin else "mac" if isMac else "lin"
