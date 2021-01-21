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
print(os.getcwd())
os.chdir(str(__file__)[:-6] + os.pathsep + '..')
print(os.getcwd())

# scoredict = {}
load_dotenv()
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.guilds = True
intents.members = True
# intents.channels = True



prefix = '!'
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWD = os.getenv('EMAIL_PASSWD')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
VERIF_CHANNEL = int(os.getenv('VERIF_CHANNEL'))
client = commands.Bot(command_prefix = prefix, intents=intents)
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
    
    if 'sis' in str(message.content).lower():
        await message.channel.send('<:sisman:538985904778379294>')

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


@client.command(name='code')
async def code(ctx):
    """
    Sends a github link with my source code.
    """
    await ctx.message.channel.send('https://github.com/matt-pharr/ComputerMan')

@client.command(name='source')
async def source(ctx):
    """
    An alias for command 'code.'
    """
    await ctx.message.channel.send('https://github.com/matt-pharr/ComputerMan')

@client.command(name='unverify')
async def unverify(ctx):
    """
    Unverifies the user.
    """
    guild = client.get_guild(GUILD_ID)
    verified = discord.utils.find(lambda r: r.name == 'Verified', guild.roles)
    studentrole = discord.utils.find(lambda r: r.name == 'Students', guild.roles)
    alumnirole = discord.utils.find(lambda r: r.name == 'Alumni', guild.roles)
    user = discord.utils.find(lambda m: m.id == ctx.message.author.id, guild.members)

    await user.remove_roles(verified,studentrole,alumnirole)


@client.command(name='verify')
async def verify(ctx):
    """
    Completes the verification process for unverified users. Checks the directory to ensure user is a student, then sends an email with a verification code to user's rpi email address. Your name or discord handle are never shared with the public or RPI.
    """

    ## Checks that the user is not already verified in the operating server:

    guild = client.get_guild(GUILD_ID)
    verified = discord.utils.find(lambda r: r.name == 'Verified', guild.roles)
    user = discord.utils.find(lambda m: m.id == ctx.message.author.id, guild.members)

    if verified in user.roles and not user.guild_permissions.administrator:# and False:
        await ctx.message.channel.send("You are already verified. If this is a mistake, please contact staff.")
        return
    
    ## Sends an instructional DM to the user:

    channel = await ctx.message.author.create_dm()
    mymessage = await channel.send('Type your RCS id (ex: \'persap\') or RPI email to verify your identity. You will recieve an email to your RPI inbox with a six-digit verificaion code.')
    
    if channel != ctx.message.channel:
        await ctx.message.channel.send("DM Sent.")
    
    print('verifying ' + str(ctx.message.author))

    ## Waits for user to send their rcs id or email. Checks that the next message is not from the bot:

    rcs_msg = await client.wait_for('message', check = lambda message: (message.channel == channel))
    if rcs_msg.author == mymessage.author:
        return
    rcs_msg = str(rcs_msg.content).strip()
    print('rcs id = ' + rcs_msg)

    ## Processes the message and determines whether it is a valid ID/email: 

    if rcs_msg[-8:] == '@rpi.edu':
        email = rcs_msg
        rcs = rcs_msg[:-8]
    elif '@' in rcs_msg:
        print('invalid email address ' + str(user))
        await channel.send(rcs_msg + ' is an invalid e-mail address. Please type !verify to try again.')
        return
    elif re.match('^[a-z]{2,7}[0-9]*$',rcs_msg) is not None:
        email = rcs_msg + '@rpi.edu'
        rcs = rcs_msg
    elif rcs_msg[0] == prefix:
        print(str(user) + ' quit verification')
        return
    else:
        print(str(user) + ' inputted invalid id')
        await channel.send('Not a valid RCS ID or rpi email. Please type !verify to try again.')
        return

    ## Searches the directory and checks whether the given RCS id is a student:

    dsearch = await directorysearch.check_is_student(rcs)

    if not dsearch[0]:
        role = dsearch[1].replace('&amp;','&')
        name = dsearch[2]
        print(str(user) + ' inputted non-student id')
        await channel.send(name + ' is not a student. Your role is ' + role + '.')
        return

    await channel.send("Sending verification email to " + email + '. Make sure to check your spam folder at https://respite.rpi.edu/canit/index.php if it does not show up in your inbox immediately.\n\nPlease type in the recieved six-digit verification code.')
    
    ## Generates a code and email content:

    code = str(random.randint(0,999999)).zfill(6)
    print('code:', code)
    text_subtype = 'plain'
    content = "Dear community member,\n\nYour verification code is %s. If you did not request a code, please disregard this email.\n\nSincerely,\n\nCommunity Coordinator Team." % code
    
    sender = EMAIL_USER
    destination = email
    subject = 'RPI Student Discord Verification'

    ## MIME formats and sends the email using the given email username and password:

    try:
        msg = MIMEText(content,text_subtype)
        msg['Subject'] = subject
        msg['From'] = 'Community Discord Verification <' + sender + '>'
        msg['To'] = dsearch[2] + ' <' + destination + '>'
        msg['Date'] = formatdate(usegmt=True)

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
        print('email not sent to ' + str(user))
        return

    print('waiting...')

    ## Waits for verification code and checks that the code is correct:
    code_msg = await client.wait_for('message', check = lambda message: (message.channel == channel))
    print("code recieved")
    if code_msg.author == mymessage.author:
        print(str(user) + " quit verification")
        return
    code_msg = str(code_msg.content).strip()
    if code_msg != code:
        print("invalid code")
        await channel.send("Incorrect code. Type " + prefix + "verify to try again.")
        return
    ## Verifies the user:
    else:
        
        studentrole = discord.utils.find(lambda r: r.name == 'Students', guild.roles)
        await user.add_roles(verified,studentrole)      
        
        await channel.send("Thank you for verifying your student status. Your identity will never be shared with RPI or the public. You now have access to verified student/alumni-only channels.")

        newchannel = client.get_channel(VERIF_CHANNEL)
        await newchannel.send(str(rcs) + " = <@" + str(user.id) + "> (" + str(user.id) + ")")
        print(f'user {str(user)} verified as {rcs} ({dsearch[2]})')
    
    return


@client.command(name='update')
async def update(ctx):
    if ctx.message.author.guild_permissions.administrator == True:
        await ctx.send('Pulling from source...')
        os.system('git pull')
        return

@client.command(name='restart')
async def restart(ctx):
    if ctx.message.author.guild_permissions.administrator == True:
        await ctx.send('Restarting...')
        os.system('sudo reboot')
        return

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
        ctx.send("Permission Denied.")

@client.command(name='echo')
async def echo(ctx):
    if ctx.message.author.guild_permissions.administrator:
        await ctx.send(str(ctx.message.content)[6:])
        await ctx.message.delete()

client.loop.create_task(update_stats())
client.run(TOKEN)