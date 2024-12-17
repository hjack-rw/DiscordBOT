import os

test = False
if not test:
    # clone source code repository
    os.system("git clone https://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@github.com/69HJack69/DiscordBOT.git")

    # unpack it
    os.system("cp -R DiscordBOT/* .")

    # remove the created folder
    os.system("rm -rf DiscordBOT")

    # install requirements
    os.system("pip install -r main_requirements.txt")

    # run main.py
    os.system("python3 main.py")