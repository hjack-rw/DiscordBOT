# DiscordBOT

A Harry Potter themed Discord bot for community servers. Built with discord.py, featuring a house cup scoring system, XP-based leaderboard with custom-generated player cards, and a pet collection system.

![Leaderboard](screenshots/leaderboard.png)

## Features

### House Cup
- Tracks house points for Gryffindor, Hufflepuff, Ravenclaw, and Slytherin
- Leaderboard channel with automatically generated player cards

### XP & Leaderboard
- Per-message XP tracking with level progression
- Visual leaderboard cards generated with Pillow — chocolate frog card aesthetic with house-color borders, pet companions, and XP progress bars
- Admin commands: add/subtract/set XP, reset, archive, customize card display name

### Pet System
- Players answer a questionnaire to determine their personalized HP creature companions (Basilisk, Kelpie, Thestral, Ashwinder and more)
- Pets displayed on leaderboard cards
- `/suitcase` command to view your collection

### Notifications & Events
- Welcome cards for new members (custom image generated per user)
- Birthday notifications
- Scheduled house cup announcements, rotating discipline system across 4-week cycles
- Portkey system — archive and post custom introductory messages

### Admin Tooling
- DB backup / restore / remote download
- Webhook impersonation (Polyjuice Potion command)
- Optional manual notification trigger
- Maintenance scheduling

## Stack

Python · discord.py · SQLite · Pillow (image generation) · python-dotenv

## Setup

```bash
pip install -r requirements.txt
```

Create `src/env`:
```
DISCORD_TOKEN=your_token_here
DISCORD_BOT_TOKEN=your_bot_token_here
```

```bash
python _run.py
```

## Architecture

```
src/
├── body.py          # Bot client setup
├── commands.py      # Slash commands (admin + general)
├── events.py        # Event listeners
├── tasks.py         # Scheduled background tasks
├── views.py         # Discord UI components (dropdowns, buttons)
├── db.py            # Database layer
├── db_classes.py    # ORM-style model classes
├── functions.py     # Image generation, leaderboard, webhooks
└── image_module/    # Assets: fonts, templates, house crests
```
