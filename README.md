# GPO Trick-or-treat Macro
A repository that holds a macro that can automate trick-or-treating in GPO
- Built specifically for **Windows** systems.
 
## Prerequisites
- [Python](https://www.python.org/downloads/) 3.10+
- Any IDE
  - Recommended: [Visual Studio Code](https://code.visualstudio.com/)
 
## Installation Guide

### 1. Download this project as ZIP
First, press the `<> Code` button. Next, press the `Download ZIP` button

### 2. Open the project in an IDE
Open the folder in VSCode
- If you do not see `main.py`, try again and choose the correct folder

### 3. Install the required packages
```bash
python -m pip install keyboard pydirectinput pillow easyocr rapidfuzz numpy pynput
```

## Macro Setup Guide

### 1. Run the program through `main.py`
In VSCode, you might need to download the Python Extension

### 2. Edit the regions/markers
<details>
	<summary>Regions and markers descriptions</summary>
  <br>

  Depending on your `REPOSITION BY` type, you may need to edit more regions/markers

  You might need to run the macro a few times to get your Regions correct.
  
  ```
Main Game OCR
- Resize this Region such that it covers the bottom left corners' "Menu" button.
  [!] If the button is not covered fully by the Region, it might not detect if you have loaded into the game

Knock Detection
- Resize this Region such that it covers the word "Knock". Be generous with your sizing.

Exit [EXCLUSIVE TO REJOINING]
- Drag the Marker so it covers the "Exit to" button

Main Menu [EXCLUSIVE TO REJOINING]
- Within the "Exit to" dropdown, drag the marker on the "Main Menu" button

Menu Screen OCR [EXCLUSIVE TO REJOINING]
- Resize this Region such that it covers the bottom centers' "Press any key to continue" text.
  [!] If the text is not covered fully by the Region, it might not detect if you have loaded into the menu

Private Server [EXCLUSIVE TO REJOINING]
- Drag this marker on top of the "Private Servers" button

Server Code Box [EXCLUSIVE TO REJOINING]
- Drag this marker on top of the area where you would normally type in the private server code

Regular [EXCLUSIVE TO REJOINING]
- Drag this marker on top of "Regular" button
  - You need to type in a private server code to get this button to appear

First Sea [EXCLUSIVE TO REJOINING]
- Drag this marker on top of "First Sea" button
  - You need to type in a private server code to get this button to appear after clicking the "Regular" button

Fail Detection [EXCLUSIVE TO REJOINING]
- You need to cover the "Connection Failed" text in the disconnect message
  - Good luck getting this one.

Cancel [EXCLUSIVE TO REJOINING]
- Drag this marker on top of the "Cancel" button on the "Connection Failed" disconnect message
  - Good luck getting this one too.

Play [EXCLUSIVE TO REJOINING]
- Drag this marker on top of the play button when leaving the game
  - When you leave the game, you should be on the game's page, not the Roblox home page.
  - If you join the game through the Roblox Client and not the website, then you should find this button
  ```

</details>

### 3. Edit settings
Open `app/settings.py` and edit any values that needs changing.
- This includes keybinds, timing, and more
- You do not have to edit any of these values unless you want optimized results or different keybinds

## Macro Run Guide

### 1. Run the program through `main.py`
In VSCode, you might need to download the Python Extension

### 2. Choose your `Reposition By` method
If you are running 2 or more accounts at the same time, choose `Drowning`.
- You need to clear the top left side of the map before running this macro
  - Clearing as in, no enemies are on the top left side, and all enemies are spawned elsewhere

Choose `Rejoining` if you are running 1 account
- You need a private server code that is only used by you. No other accounts should be in this server.

### 3. Configuration
- Use your candy bag in slot 1 of your backpack and have another item in slot 2.
- Turn off `auto run` in GPO's settings.
- Make sure to have your camera in a reasonable distance (not too close, not too far)

### 4. Respawn all of your accounts
- This is an essential step when running the program, you can skip this step if you did not move after loading in.
- Respawn means fully dying and spawning back in. It does NOT mean resetting your character and regenerate your HP.

### 5. Run the program
- If you have fully read this document and done your setup properly, this macro should work properly.
- You can run the program through pressing the button or pressing `F7` on your keyboard
