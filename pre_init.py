import os
import sys


def run_pre_init(test_bot):
    # live server test
    if test_bot == 1:
        # clone source code repository
        os.system("git clone https://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@github.com/69HJack69/DiscordBOT.git")

        # unpack it
        os.system("cp -R DiscordBOT/* .")

        # remove the created folder
        os.system("rm -rf DiscordBOT")

        # install requirements
        os.system("pip install -r main_requirements.txt")


if __name__ == "__main__":
   run_pre_init(test_bot=sys.argv[0])
   
   # run main.py
   os.system("python3 main.py")