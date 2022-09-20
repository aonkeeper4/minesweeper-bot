import discord
from discord.ext import commands
import os
from github import Github
import toml
from keep_alive import keep_alive

git = Github(os.environ["GITHUB_TOKEN"])

intents = discord.Intents().all()
client = commands.Bot(command_prefix=";", intents=intents)

def download_asset_from_release(asset_name, release, path):
    asset = next(asset for asset in release.get_assets() if asset.name == asset_name)
    url = asset.browser_download_url
    import urllib.request
    urllib.request.urlretrieve(url, path)

@client.event
async def on_ready():
    print(f"{client.user} is ready")
    
@client.event
async def on_command_error(ctx, e):
    await ctx.send(str(e))
    
@client.command(help="starts new minesweeper game")
async def start(ctx):
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
            print("current version is the latest")
            
    # by now we should have the minesweeper.exe
    pass

@client.command()
async def stop(ctx):
    await ctx.send("stopping")
    await client.close()
    
keep_alive()
client.run(os.environ["MINESWEEPER_BOT_TOKEN"])