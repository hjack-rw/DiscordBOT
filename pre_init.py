import os
import sys


def run_pre_init(test_bot):
    # live server test
    if not test_bot:
        # clone source code repository
        os.system("git clone https://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@github.com/69HJack69/DiscordBOT.git")

        # unpack it
        os.system("cp -R DiscordBOT/* .")

        # remove the created folder
        os.system("rm -rf DiscordBOT")

        # install requirements
        os.system("pip install -r main_requirements.txt")


def if_none(variable):
    try:
        return int(sys.argv[variable]) == 1
    except IndexError:
        return False


test_bot = if_none(variable=1)
test_body = if_none(variable=2)
test_command = if_none(variable=3)
test_events = if_none(variable=4)
test_tasks = if_none(variable=5)


if __name__ == "__main__":
    run_pre_init(test_bot)

    # run main.py
    os.system("python3 main.py")