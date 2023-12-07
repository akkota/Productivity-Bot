import discord
from discord.ext import commands
import asyncio
import sqlite3
import pymongo
from dotenv import load_dotenv
import os

load_dotenv()

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

@bot.command() #You do this to open a new command!
async def pomodoro(context, studytime, breaktime, sessionnumber): 
    currentsesh = 1
    sessionnumber = int(sessionnumber)
    studytime = int(studytime)
    breaktime = int(breaktime)
    while sessionnumber > 0: 
        await context.send(context.message.author.mention + "Starting pomodoro...")
        seconds = studytime * 60
        while True:
            seconds = seconds - 1
            await asyncio.sleep(1)
            if seconds == 0:
                await context.send(context.message.author.mention + " Study session is done! Starting Break")
                break
        seconds = breaktime * 60
        while True:
            seconds = seconds - 1
            await asyncio.sleep(1)
            if seconds == 0:
                await context.send(context.message.author.mention + " Break is done!")
                await context.send(context.message.author.mention + " You have completed pomodoro number " + str(currentsesh) + "!")
                sessionnumber = sessionnumber - 1
                currentsesh = currentsesh + 1
                break


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

