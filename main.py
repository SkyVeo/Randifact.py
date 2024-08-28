import nextcord
from nextcord.ext import commands, tasks
import requests

from datetime import datetime, timezone
import os
from random import choice

from keep_alive import keep_alive

intents = nextcord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix="rf!", intents=intents)
client.remove_command("help")


def read_file(*files: str) -> list:
    facts = []
    for file in files:
        with open(f"{file}.txt", encoding="utf-8") as f:
            facts += [fact.rstrip("\r\n ") for fact in f.readlines() if fact.rstrip("\r\n ") != "" and len(fact) <= 128]

    return facts


fact = None
facts = read_file("safe", "randifact")

test_guild_ids = [767386665701605379, 700086135384309811]
vote_link = "https://top.gg/bot/981651003558481994/vote"


class VoteButtonView(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        button = nextcord.ui.Button(url=vote_link, label="Vote here for bonus fun facts")
        self.add_item(button)


async def update_fact() -> None:
    global fact

    fact = choice(facts)
    await client.change_presence(activity=nextcord.Game(name=fact))


@client.event
async def on_ready():
    if datetime.now(timezone.utc).minute != 0:
        await update_fact()
    facts_loop.start()


@tasks.loop(seconds=60)
async def facts_loop():
    if datetime.now(timezone.utc).minute == 0:
        await update_fact()


async def send_guild_update(guild: nextcord.Guild, action: str) -> None:
    test_guild = client.get_guild(test_guild_ids[0])
    channel = nextcord.utils.get(test_guild.channels, id=905201481202954240)
    if channel and guild and guild.name:
        await channel.send(f"{action} `{guild.name}` with `{len(guild.members)}` members")


@client.event
async def on_guild_join(guild: nextcord.Guild):
    await send_guild_update(guild, "Joined")


@client.event
async def on_guild_remove(guild: nextcord.Guild):
    await send_guild_update(guild, "Left")


async def check_vote(user: nextcord.Member) -> bool:
    try:
        request_text = requests.get(
            f"https://top.gg/api/bots/981651003558481994/check?userId={user.id}",
            headers={"Authorization": os.environ["topgg_token"]},
        ).text
    except Exception as e:
        print(f"An error occured while checking the website:\n{e}")
        return False

    return "voted" in request_text and "1" in request_text


@client.slash_command(name="fun", description="Display the current fun fact")
async def fun(interaction: nextcord.Interaction):
    pass


@fun.subcommand(name="fact", description="Display the current fun fact")
async def fun_fact(interaction: nextcord.Interaction):
    await interaction.response.defer()

    embed = nextcord.Embed(color=nextcord.Color.dark_green())
    embed.set_author(name=fact, icon_url=client.user.avatar)

    if await check_vote(interaction.user):
        embed.set_footer(text=f"Bonus fun fact because you voted\n{choice(facts)}")

    await interaction.send(embed=embed, view=VoteButtonView())


@client.slash_command(name="help", description="I have a help command, that's a fact")
async def help(interaction: nextcord.Interaction):
    await interaction.send(f"Click on {client.user.mention} to learn a fact every hour", ephemeral=True)


@client.slash_command(name="vote", description="A little bit of support will be appreciated")
async def vote(interaction: nextcord.Interaction):
    await interaction.send(f"[]({vote_link})", ephemeral=True)


keep_alive()
client.run(os.environ["token"])
