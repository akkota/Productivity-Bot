import discord
from discord.ext import commands
import asyncio
import sqlite3
import pymongo
from dotenv import load_dotenv
import os

load_dotenv()
#global variables used for pomodoro and finish pomodoro method
currentsesh = 0
originalsessionnumber = 0
stoppomodoro = False
midpomodoro = False

intents = discord.Intents.all() 
bot = commands.Bot(command_prefix="!", intents=intents)
databaselink = os.getenv("DATABASE")
client = pymongo.MongoClient(databaselink)
myDB = client["DiscordBot"]

@bot.event
async def on_ready(): 
    print("Bot is ready for use!")

@bot.command() #You do this to open a new command!
async def hello(context): 
    await context.send("Hello it's the bot lol")

pomodorocollection = myDB["Pomodoros"]
@bot.command() #You do this to open a new command!
async def pomodoro(context, studytime, breaktime, sessionnumber): 
    global currentsesh
    global originalsessionnumber
    global stoppomodoro
    global midpomodoro
    currentsesh = 1
    originalsessionnumber = int(sessionnumber)
    sessionnumber = int(sessionnumber)
    studytime = int(studytime)
    breaktime = int(breaktime)
    totalstudytime = 0
    stoppomodoro = False
    while not stoppomodoro: 
        midpomodoro = True
        await context.send(context.message.author.mention + "Starting pomodoro...")
        seconds = studytime * 60
        while True and midpomodoro:
            seconds = seconds - 1
            await asyncio.sleep(1)
            totalstudytime = totalstudytime + 1
            if seconds == 0:
                await context.send(context.message.author.mention + " Study session is done! Starting Break")
                sessionnumber = sessionnumber - 1
                currentsesh = currentsesh + 1
                break
            if stoppomodoro: 
                midpomodoro = False
                break
        seconds = breaktime * 60
        while True and midpomodoro:
            seconds = seconds - 1
            await asyncio.sleep(1)
            if seconds == 0:
                await context.send(context.message.author.mention + " Break is done!")
                await context.send(context.message.author.mention + " You have completed pomodoro number " + str(currentsesh - 1) + "!")
                break
            if stoppomodoro: 
                midpomodoro = False
                break
        if sessionnumber == 0: 
            stoppomodoro = True
    await context.send("Recording study time " + str(round((totalstudytime/60), 1)) + " minutes")
    if (pomodorocollection.find_one({"user": context.message.author.name, "studytime": {"$exists": True}})):
        pomodorocollection.update_one({"user": context.message.author.name}, {"$inc": {"studytime": round((totalstudytime/60), 1)}})
    else:
        pomodorocollection.insert_one({
            "user": context.message.author.name,
            "serverid": context.message.guild.id,
            "studytime": round((totalstudytime/60), 0)
        })    
    stoppomodoro = True   
    
@bot.command()
async def finishpomodoro(context): 
    global currentsesh
    global originalsessionnumber
    global stoppomodoro
    if (midpomodoro and (currentsesh - 1 < originalsessionnumber)): 
        await context.send(context.message.author.mention + " You have only completed " + str(currentsesh-1) + " pomodoros.")
        stoppomodoro = True 
    else: 
        await context.send(context.message.author.mention + " You have not started a pomodoro yet!")    

@bot.command()
async def leaderboard(context): 
    users = []
    time = []
    serverid = context.message.guild.id
    serverfiltercollection = pomodorocollection.find({"serverid": context.message.guild.id})   
    for user in serverfiltercollection: 
        users.append(user.get("user"))
        time.append(user.get("studytime"))
    combined_zippedlist = list(zip(time, users)) #this combines the lists users and time
    combined_zippedlist.sort() #this sorts combined_list according to time (as it was the first parameter)
    sorted_users = []
    sorted_time = []
    for (a,b) in combined_zippedlist: 
        sorted_users.append(b)
        sorted_time.append(a)
    embedmessage = discord.Embed(title="Leaderboard", color=0xffd700)
    if (len(sorted_users) == 0):
        embedmessage.add_field(name = "BOOOOOOOOO", value = "No one has studied yet :(")
    if (len(sorted_users) >= 1):
        embedmessage.add_field(name = "First Place", value = sorted_users[len(sorted_users) - 1] + "\n" + "StudyTime - " + str(round((sorted_time[len(sorted_time) - 1])/60, 1)) + " hours", inline=False)
    if (len(sorted_users) >= 2):
        embedmessage.add_field(name = "Second Place", value = sorted_users[len(sorted_users) - 2] + "\n" + "StudyTime - " + str(round((sorted_time[len(sorted_time) - 2])/60, 1)) + " hours", inline=False)
    if (len(sorted_users) >= 3):
        embedmessage.add_field(name = "Third Place", value = sorted_users[len(sorted_users) - 3] + "\n" + "StudyTime - " + str(round((sorted_time[len(sorted_time) - 3])/60, 1)) + " hours", inline=False)
    await context.send(embed=embedmessage)

taskcollection = myDB["Tasks"]
@bot.command()
async def addtask(context, taskname, description): 
    taskcollection.insert_one(
        {
            "user": context.message.author.name, 
            "task": taskname,
            "description": description
        }
    )
    await context.send("Successfully added a task, " + taskname)

@bot.command()
async def viewtasks(context): # Still have to check if this works!
    embedmessage = discord.Embed(title="Tasks - " + context.message.author.name, color=0x00ff00)
    alltasks = taskcollection.find({"user": context.message.author.name})
    count = 1
    for object in alltasks: #this loops through every object
        embedmessage.add_field(name="Task " + str(count), value="Taskname -> " + object.get('task') + "\n" + "Description -> " + object.get('description'), inline=False)
        count = count + 1
    if (count == 1): 
        await context.send(context.message.author.mention + " you don't have tasks!")
    else: 
        await context.send(embed=embedmessage)  

@bot.command()
async def finishtask(context, taskname): 
    if(taskcollection.find_one({"user": context.message.author.name, "task": taskname})): 
        taskcollection.delete_one({"user": context.message.author.name, "task": taskname})
        await context.send(context.message.author.mention + " Good job finishing " + taskname)
    else: 
        await context.send(context.message.author.mention + " That task does not exist!")
        
bot.run(os.getenv("TOKEN"))

