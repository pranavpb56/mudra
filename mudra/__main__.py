import argparse

from . import __version__, config


def main():
    p = argparse.ArgumentParser(prog="mudra", description="Control your Mac with your hands and your voice.")
    p.add_argument("command", nargs="?", default="run", choices=["run", "init"])
    p.add_argument("--no-preview", action="store_true", help="hide the camera window")
    p.add_argument("--no-voice", action="store_true", help="disable voice commands")
    p.add_argument("--camera", type=int, default=None, help="camera index")
    p.add_argument("--version", action="version", version=__version__)
    a = p.parse_args()
    if a.command == "init":
        print(f"Config ready at {config.init_user_config()}")
        return
    from .app import run
    run(config.load(), preview=not a.no_preview, voice=not a.no_voice, camera=a.camera)


if __name__ == "__main__":
    main()
