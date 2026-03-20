from .app import YapPad
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--slim",
        "-s",
        action="store_true",
        help="flag to run the app without creating transcription models in memory",
    )
    return parser.parse_args()


# entry point
if __name__ == "__main__":
    args = parse_args()
    app = YapPad(args)
    app.run()
