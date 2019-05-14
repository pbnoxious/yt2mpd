import argparse

def setup_parser():
    """Definitions of all cli arguments for the argparser"""
    parser = argparse.ArgumentParser(
            description = "Fetch audio from youtube and play it via mpd.",
            prog = "youtube-to-mpd"
            )

    self.parser.add_argument("-s", metavar="song", help="ID or URL of song")
