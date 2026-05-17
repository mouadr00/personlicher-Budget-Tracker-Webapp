"""Command line entrypoint for the NiceGUI app."""

from .application import BudgetTrackerApplication


def main() -> None:
    BudgetTrackerApplication().run()


if __name__ == "__main__":
    main()
