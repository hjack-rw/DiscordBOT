import os
import readchar

from cutie  import DefaultKeys
from typing import List, Optional


__all__ = ["test_bot"]


def system_variable():
    return os.getenv("GIT_CLONE") == "True"

def flavor(string, options=["bold",], end=True):
    font = {type: f"\033[{code}m" for (type, code) in [("blue", "34"), ("yellow", "33"), ("green", "32"), ("red", "31"), ("cyan", "36"), ("white", "37"), ("black", "30"), ("negative", "7"), ("underline", "4"), ("grey", "2"), ("bold", "1"), ("end", "0")]}

    # add code for formatting
    modifiers = "".join([font[option] for option in options])
    modified_string = modifiers + string

    # reset to normal text after
    if end:
        return modified_string + font["end"]
    else:
        return modified_string

def select_multiple(options: List[str],
                    caption_indices: Optional[List[int]] = None,
                    deselected_unticked_prefix: str = "( )",
                    deselected_ticked_prefix: str = flavor("("+ flavor("x", options=["green"], end=False)) + flavor(")"),
                    selected_unticked_prefix: str =  "< >",
                    selected_ticked_prefix: str = flavor("<"+ flavor("x", options=["green"], end=False))  + flavor(">"),
                    caption_prefix: str = "",
                    ticked_indices: Optional[List[int]] = None,
                    cursor_index: int = 1,
                    minimal_count: int = 0,
                    maximal_count: Optional[int] = None,
                    hide_confirm: bool = False,
                    deselected_confirm_label: str = " Continue\n\n",
                    selected_confirm_label: str = flavor(" Continue\n\n"),
                    key_bindings = DefaultKeys) -> List[int]:

    print("\n" * (len(options) - 1))
    
    if caption_indices is None:
        caption_indices = []
    if ticked_indices is None:
        ticked_indices = []
    
    max_index = len(options) - (1 if hide_confirm else 0)
    error_message = ""
    
    skip_first = True

    while True:
        if not skip_first:
            print("".join(["-" for _ in range(30)]))
        else:
            skip_first = False

        for i, option in enumerate(options):
            prefix = ""
            if i in caption_indices:
                prefix = caption_prefix
            elif i == cursor_index:
                if i in ticked_indices:
                    prefix = selected_ticked_prefix
                else:
                    prefix = selected_unticked_prefix
            else:
                if i in ticked_indices:
                    prefix = deselected_ticked_prefix
                else:
                    prefix = deselected_unticked_prefix
            print("{} {}".format(prefix, flavor(option, options=["end"], end=False)))
        
        if hide_confirm:
            print(f"{error_message}", end="", flush=True)
        else:
            if cursor_index == max_index:
                print(f"{selected_confirm_label} {error_message}", end="", flush=True,)
            else:
                print(f"{deselected_confirm_label} {error_message}", end="", flush=True,)
        
        error_message = ""
        keypress = readchar.readkey()
        
        if keypress in key_bindings.up:
            new_index = cursor_index
            while new_index > 0:
                new_index -= 1
                if new_index not in caption_indices:
                    cursor_index = new_index
                    break
        elif keypress in key_bindings.down:
            new_index = cursor_index
            while new_index + 1 <= max_index:
                new_index += 1
                if new_index not in caption_indices:
                    cursor_index = new_index
                    break
        elif (hide_confirm and keypress in key_bindings.confirm or not hide_confirm and cursor_index == max_index):
            if minimal_count > len(ticked_indices):
                error_message = f"Must select at least {minimal_count} options"
            elif maximal_count is not None and maximal_count < len(ticked_indices):
                error_message = f"Must select at most {maximal_count} options"
            else:
                break
        elif (keypress in key_bindings.select or not hide_confirm and keypress in key_bindings.confirm):
            if cursor_index in ticked_indices:
                ticked_indices.remove(cursor_index)
            else:
                ticked_indices.append(cursor_index)
        elif keypress in key_bindings.interrupt:
            raise KeyboardInterrupt
    
    print("\r", end="", flush=True)
    return ticked_indices

git_clone = system_variable()

if __name__ == "__main__":

    if git_clone:
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

else:
    test_bot = {"local_deploy": False if (os.getcwd() == "/home/container") else True,
                "test_body":    False,
                "test_command": False,
                "test_events":  False,
                "test_tasks":   False,}

    # live server test
    if not git_clone:
        key_bindings = DefaultKeys
        key_bindings.up = ["w"]
        key_bindings.down = ["s"]
        key_bindings.confirm = ["d"]
        
        print("\n")
        print(f"up: {key_bindings.up}")
        print(f"down: {key_bindings.down}")
        print(f"enter: {key_bindings.confirm}")
        print("".join(["-" for _ in range(30)]))

        indices = select_multiple(options=[(option if option != "local_deploy" else f"local_deploy: {test_bot['local_deploy']}") for option in test_bot.keys()] + [" "],
                                  caption_indices=[0, len(test_bot)], key_bindings=key_bindings,)
        test_bot = {key:(value if idx not in indices else True) for idx,(key,value) in enumerate(test_bot.items())}