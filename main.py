import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image,ImageFont,ImageDraw
import os
import random
import io
import requests
import shutil

path = os.path.dirname(__file__)    
with open(os.path.join(path,'token.txt'), 'r') as file:
    TOKEN = file.read().rstrip()
    file.close()
bot = commands.Bot(command_prefix="mrbeast.",intents = discord.Intents.all())

# FONT1 - Monospaced username font.
# FONT2 - Main text font.
# FONT3 - Font for the "x minutes ago" text. 
FONT1 = ImageFont.truetype(os.path.join(path, 'RobotoMono-Bold.ttf'), 13)
FONT2 = ImageFont.truetype(os.path.join(path, 'Roboto-Medium.ttf'), 15)
FONT3 = ImageFont.truetype(os.path.join(path, 'Roboto-Medium.ttf'), 12)

@bot.event
async def on_ready():
    print("mr beast assembled")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.tree.command(name="slop")
@app_commands.describe(mode = "Use text mode ('text') to read plain messages, otherwise leave blank to read starboard embeds")
async def slop(interaction: discord.Interaction,mode: str = None):
    await interaction.response.defer()
    channel = bot.get_channel(int(111111111111)) # Channel id goes here. Todo add channel selector
    messages = []
    names = []
    ids = []
    async for message in channel.history(limit=1000):

        # Message embeds are stored in an array to allow messages to have more than 1 embed attached.
        # If the embedded message being posted to starboard is a reply to another message, then the message being replied to is also embedded.
        # [len(message.embeds)-1] ensures only the last embed is read. This is not necessary for text mode, as normal messages omly return str.
        # Deleted users are always ignored. Better error checking for invalid users/ids could be implemented.
        if mode != "text":
            if message.embeds != [] and message.author.name != "Deleted User#0000":
                messages.append(message.embeds[len(message.embeds)-1].description)
                names.append(message.embeds[len(message.embeds)-1].author.name)
                idRaw = message.embeds[len(message.embeds)-1].author.icon_url
                idTrimmed = await urlToID(idRaw)
                ids.append(idTrimmed)

        else:
            if message.content != "" and str(message.author) != "Deleted User#0000":
                messages.append(message.content)
                names.append(message.author)
                id = message.author.id
                ids.append(str(id))

    bg = await getVideo()
    await writeComments(messages,names,ids,bg)
    # If resizing the image made it appear bigger (at the cost of appearing more pixelated) I would put...
    # bg = bg.resize((int(float(bg.size[0])*1.25),int(float(bg.size[1])*1.25)))
    # ...here. However only aspect ratio is taken into account when displaying images in chat on pc from what I can tell.
    with io.BytesIO() as image_binary:
        bg.save(image_binary, 'PNG')
        image_binary.seek(0)
        await interaction.followup.send(file=discord.File(fp=image_binary, filename='image.png'))

async def urlToID(idRaw):

    # Getting a user ID from a message is as simple as message.author.id. However message authors in embedded messages don't have an ID object.
    # Instead, the user's avatar url is passed to this function, where the section containing the user's ID is trimmed out.
    start = '/avatars/'
    end = '/'
    idTrimmed = idRaw[idRaw.find(start)+len(start):idRaw.rfind(end)]

    # ...However, users with a nitro server profile have an entirely different url.
    # If the first url trim cannot find the ID, then it is checked again with a different start and end point that matches those alternaute urls.
    if idTrimmed == "":
        start = '/users/'
        end = '/avatars'
        idTrimmed = idRaw[idRaw.find(start)+len(start):idRaw.rfind(end)]
    return str(idTrimmed)


async def getVideo():
    video = random.randint(0,14)
    bg = Image.open(os.path.join(path, ("videos/thumbnail"+str(video)+".png")))
    return bg


async def createComment(name,text,id,pos,bg):
    comment = Image.open(os.path.join(path, 'videos/template.png'))
    name = "@"+str(name)
    timePadding = 0 + len(name)
    commentTime = str(random.randint(1,5))+" minutes ago"

    ImageDraw.Draw(comment).text((66, 12),name,(241,241,241),font=FONT1)
    ImageDraw.Draw(comment).text((66, 35),text,(241,241,241),font=FONT2)
    ImageDraw.Draw(comment).text(((66+(timePadding*8)+3), 14),commentTime,(158,158,158),font=FONT3)
    bg.paste(comment,pos)

    # After going through the process of converting a url into an id, the id is then used to fetch the user...
    # ...and then the user's avatar url is taken from the user. This time its always a consistent url which can be fetched using requests.
    # This image request is then copied to a .png file that PIL is finally happy to accept. 
    user = await bot.fetch_user(id)
    avatar = requests.get(user.avatar,stream=True)
    with open(os.path.join(path,"image.png"), 'wb') as out:
        shutil.copyfileobj(avatar.raw,out)
    avatarImg = Image.open(os.path.join(path,"image.png"))

    # Creates a circle mask for the avatar, resizes both, pastes the masked avatar onto the base image.
    bigsize = (avatarImg.size[0] * 3, avatarImg.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + bigsize, fill=255)
    avatarImg = avatarImg.resize((40,40))
    mask = mask.resize(avatarImg.size)
    pos = (pos[0]+12,pos[1]+12)
    bg.paste(avatarImg,pos,mask=mask)

async def writeComments(messages,names,ids,bg):
    for i in range(7):
        pos = (7,(810+(90*i)))
        j = random.randint(0,(len(messages)-1))
        message = messages[j]
        name = names[j]
        id = ids[j]
        await createComment(name,message,id,pos,bg)
bot.run(TOKEN)