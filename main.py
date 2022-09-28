import discord
from discord.ext import commands
import os
from github import Github
import toml
from keep_alive import keep_alive
from subprocess import Popen, PIPE
import asyncio

git = Github(os.environ["GITHUB_TOKEN"])

intents = discord.Intents().all()
client = commands.Bot(command_prefix=";", intents=intents)

def download_asset_from_release(asset_name, release, path):
    asset = next(asset for asset in release.get_assets() if asset.name == asset_name)
    url = asset.browser_download_url
    import urllib.request
    urllib.request.urlretrieve(url, path)
    
async def send_embed(ctx, title, body, colour, r=False, footer='', edit=None):  # helper function cus embeds are pain
    embed = discord.Embed(title=title, description=body, colour=colour)
    embed.set_footer(text=footer)
    if edit is None:
        msg = await ctx.send(embed=embed)
    else:
        msg = edit
        await edit.edit(embed=embed)
    return msg if r else None    

async def wait_for_message(ctx, check, timeout=60):  # another helper function weeee
    try:
        message = await client.wait_for(
            'message',
            timeout=timeout,
            check=check
        )
    except asyncio.TimeoutError:
        await send_embed(
            ctx,
            'Error',
            'Error - command timed out',
            discord.Colour.red()
        )
        return
    else:
        return message

@client.event
async def on_ready():
    print(f"{client.user} is ready")
    
@client.event
async def on_command_error(ctx, e):
    await ctx.send(str(e))
    
@client.command(help="starts new minesweeper game")
async def start(ctx, width, height, num_mines, variant):
    try:
        print("finding minesweeper repo")
        minesweeper = next(repo for repo in git.get_user().get_repos() if repo.name == "minesweeper")
    except StopIteration:
        raise RuntimeError("unable to find minesweeper repository")
    
    print("gettting latest release version")
    latest = minesweeper.get_latest_release()
    latest_version = latest.id
    if not os.path.exists("./minesweeper/minesweeper.exe"):
        print("exe doesn't exist, writing toml file")
        with open("./minesweeper/minesweeper.toml", "w") as f:
            f.write(toml.dumps({"version": latest_version}))
        print("downloading latest release")
        download_asset_from_release("minesweeper.exe", latest, "./minesweeper/minesweeper.exe")
    else:
        print("getting current version")
        try:
            with open("./minesweeper/minesweeper.toml", "r") as f:
                parsed = toml.load(f)
        except FileNotFoundError:
            print("toml file doesn't exist, writing it")
            with open("./minesweeper/minesweeper.toml", "w") as f:
                f.write(toml.dumps({"version": latest_version}))
            latest_hosted = latest_version
        else:
            latest_hosted = parsed.get("version")
        
        if latest_hosted != latest_version:
            print("current version is not the latest, downloading latest release")
            download_asset_from_release("minesweeper.exe", latest, "./minesweeper/minesweeper.exe")
        else:
            print("minesweeper.exe up to date")
            
    # by now we should have the minesweeper.exe
    
    args = ["./minesweeper/minesweeper.exe", width, height, num_mines, variant]
    process = Popen(args, stdout=PIPE, stdin=PIPE)
    while not process.poll():
        stdin = wait_for_message(ctx, lambda msg: msg.author == ctx.author)
        stdout, stderr = process.communicate()
        if not stderr:
            await send_embed(ctx, "Minesweeper", f"```{stdout}```", discord.Colour.brand_green())
        else:
            await send_embed(ctx, "Minesweeper - Error", f"```{stderr}```", discord.Colour.red())
            
    await send_embed(ctx, "Game ended", f"Game has ended!", discord.Colour.brand_green())

@client.command()
async def stop(ctx):
    await ctx.send("stopping")
    await client.close()
    
keep_alive()
client.run(os.environ["MINESWEEPER_BOT_TOKEN"])