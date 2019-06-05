import argparse

class CliArguments:
    """
    Store and process CLI arguments given at execution

    Attributes:
        config_path: String holding custom path to config file
        identifier: ID or URL of song or playlist
        (searchstring: allow searching for songs using --default-search?)
        parser: argparser
    """

    def __init__(self):
        self.config_path = None
        self.identifier = None
        self.parser = None
        self.setup_parser()
        self.parse_arguments()

    def setup_parser(self):
        """Definitions of all cli arguments for the argparser"""
        self.parser = argparse.ArgumentParser(
            description = "Fetch audio from youtube and play it via mpd.",
            prog = "yt2mpd"
            )

        self.parser.add_argument("-i", metavar="identifier",
                                 help="ID or URL of youtube video or playlist", required=True)
        self.parser.add_argument("-c", metavar="config_path",
                                 help="Path to config file")

    def parse_arguments(self):
        """Process cli arguments and store them in class attributes"""
        args = self.parser.parse_args()
        self.identifier = args.i
        if args.c is not None:
            self.config_path = args.c
