import discord
from discord.ext import commands
import os
import sys
from dotenv import load_dotenv
import asyncio
import json
import random
import datetime
from locallib import directorysearch
import re
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

# scoredict = {}
load_dotenv()
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWD = os.getenv('EMAIL_PASSWD')
TOKEN = os.getenv('DISCORD_TOKEN')
client = commands.Bot(command_prefix = '!')
currentguild = 'rpi'


@client.event
async def on_ready():
    global scoredict
    print("Bot is ready.")
    print("Logged in as", client.user.display_name)
    try:
        x = datetime.datetime
        os.system('cp data/scores.json data/scores.json.' + str(x.now()).replace(' ','-') + '.bak')
        with open("data/scores.json", 'r') as f:
            scoredict = json.load(f)
    except Exception as e:
        print(e)
    # print("Scores:")
    # print(scoredict)
             

@client.event
async def on_message(message):
    global scoredict
    # Triggers whenever a message is sent in a channel the bot has access to view, in all guilds.
    if currentguild == str(message.guild):
        if message.author.bot:
            return
        if str(int(message.author.id)) in scoredict:
            scoredict[str(int(message.author.id))] += 1
        else:
            scoredict[str(int(message.author.id))] = 1
    # print(message.author.id)
    # user = client.get_user(message.author.id)
    # print(client.is_closed)
    # print(message.guild)
    # print(str(user))
    # print(scoredict)
    await client.process_commands(message)

async def update_stats():
    await client.wait_until_ready()
    await asyncio.sleep(15)
    print('stats updater running')
    global scoredict
    while True:
        print('log set')
        try:
            with open("data/scores.json", 'w') as f:
                # print(scoredict)
                json.dump(scoredict,f)
        except Exception as e:
            print(e)
        await asyncio.sleep(1800)

@client.command(name='source')
async def source(ctx):
    await ctx.message.channel.send('https://github.com/matt-pharr/ComputerMan')

@client.command(name='verify')
async def verify(ctx):
    verified = discord.utils.find(lambda r: r.name == 'Verified', ctx.message.guild.roles)
    if verified in ctx.message.author.roles and False:
        await ctx.message.channel.send("You are already verified. If this is a mistake please contact staff.")
        return
    channel = await ctx.message.author.create_dm()
    await channel.send('Type your RCS id (ex: \'persap\') or RPI email to verify your identity. You will recieve an email to your RPI inbox with a six-digit verificaion code.')
    print('verifying ' + str(ctx.message.author))
    rcs_msg = await client.wait_for('message', check = lambda message: (message.channel == channel and message.author == ctx.message.author))
    rcs_msg = str(rcs_msg.content).strip()
    print(rcs_msg)

    if rcs_msg[-8:] == '@rpi.edu':
        email = rcs_msg
        rcs = rcs_msg[:-8]
    elif '@' in rcs_msg:
        await channel.send(rcs_msg + ' is an invalid e-mail address. Please type !verify to try again.')
        return
    elif re.match('^[a-z]{2,6}[0-9]*$',rcs_msg) is not None:
        email = rcs_msg + '@rpi.edu'
        rcs = rcs_msg
    else:
        await channel.send('Not a valid RCS ID or rpi email. Please type !verify to try again.')
        return

    dsearch = await directorysearch.check_is_student(rcs)

    if not dsearch[0]:
        role = dsearch[1].replace('&amp;','&')
        name = dsearch[2]
        await channel.send(name + ' is not a student. Your role is ' + role + '.')
        return

    await channel.send("Sending verification email to " + email + '. Make sure to check your spam folder at https://respite.rpi.edu/canit/index.php if it does not show up in your inbox immediately.\n\nPlease type in the recieved six-digit verification code.')
    

    code = str(random.randint(0,999999)).zfill(6)
    print('code:', code)
    text_subtype = 'plain'
    content = "Your six-digit verification code code is %s. Return to the app to complete the verification process.\n\nIf you did not request verification on the RPI Student Discord server, you may safely disregard this message.\n\nThanks,\n\nThe RPI Student Server Moderation Team." % code
    
    sender = GMAIL_USER
    destination = email
    subject = 'RPI Student Discord Verification'

    try:
        msg = MIMEText(content,text_subtype)
        msg['Subject'] = subject
        msg['From'] = 'Computer Man <' + sender + '>'
        msg['To'] = dsearch[2] + ' <' + destination + '>'

        server = smtplib.SMTP_SSL('smtp.mailgun.org', 465)
        server.set_debuglevel(False)
        server.login(EMAIL_USER,EMAIL_PASSWD)

        try:
            server.sendmail(sender,destination,msg.as_string())
        
        finally:
            server.close()
        
        print('Email sent.')

    except Exception as e1:
        print(e1)

@client.command(name='clear')
async def clear(ctx,number = 0):
    if str(ctx.channel) != 'bots':
        pass#return -1
    print('clearing ' + str(ctx.author) + ' in channel (' + str(ctx.channel) + ', ' + str(ctx.guild) + ') times ' + str(number))
    def is_requester(msg):
        if msg.author == ctx.author:
            return True
        else:
            return False
    
    async with ctx.typing():
        deleted = await ctx.channel.purge(limit=(number+1),check=is_requester,bulk=True)
    
    print('done clearing ' + str(ctx.author) + ' in channel (' + str(ctx.channel) + ', ' + str(ctx.guild) + ') times ' + str(number))
    await ctx.send(r':white_check_mark: deleted ' + str(len(deleted)) + ' messages')

@client.command(name='isstudent')
async def isstudent(ctx,rcs):
    if ctx.message.author.guild_permissions.administrator:
        # print()
        studenthood = await directorysearch.check_is_student(rcs.split('@rpi.edu')[0])
        print(studenthood,rcs)
        if studenthood[0]:
            s1 = 'Student'
        else:
            s1 = studenthood[1].replace('&amp;','&')
        message = await ctx.send(rcs + '\'s role is ' + s1 + '.')
        await asyncio.sleep(10)
        await message.delete()
        await ctx.message.delete()
    else:
        message = await ctx.send('Permission denied.')
        await asyncio.sleep(10)
        await message.delete()
        await ctx.message.delete()

@client.command(name='botclear')
async def botclear(ctx,number):
    if ctx.message.author.guild_permissions.administrator:
        ms1 = await ctx.send('Clearing ' + str(number) + ' of my own messages...')
        print('clearing ' + str(ms1.author) + ' in channel (' + str(ctx.channel) + ', ' + str(ctx.guild) + ') times ' + str(number))
        def is_requester(msg):
            if msg.author == ms1.author:
                return True
            else:
                return False
        
        async with ctx.typing():
            deleted = await ctx.channel.purge(limit=(number+1),check=is_requester,bulk=True)
        
        print('done clearing ' + str(ms1.author) + ' in channel (' + str(ctx.channel) + ', ' + str(ctx.guild) + ') times ' + str(number))
        await ctx.send(r':white_check_mark: deleted ' + str(len(deleted)) + ' messages')
    else:
        pass    

@client.command(name='echo')
async def echo(ctx):
    if ctx.message.author.guild_permissions.administrator:
        await ctx.send(str(ctx.message.content)[6:])
        await ctx.message.delete()

client.loop.create_task(update_stats())
client.run(TOKEN)