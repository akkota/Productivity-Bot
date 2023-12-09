import discord
import requests
from discord.ext import commands
import asyncio
import sqlite3
import pymongo
from dotenv import load_dotenv
import os
import random
import json

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

@bot.command()
async def motivation(context): 
    username = context.message.author.name
    #all quotes from https://github.com/TamoStudy/TamoBot/blob/main/apps/misc/motivation.py
    messages = [
            f"You got this, **{username}**!",
            f"Believe in yourself, **{username}**!",
            f"Keep pushing forward, **{username}**!",
            f"Stay strong, **{username}**!",
            f"You're capable of great things, **{username}**!",
            f"Don't give up, **{username}**!",
            f"Take it one step at a time, **{username}**!",
            f"You're making progress, **{username}**!",
            f"Stay focused and determined, **{username}**!",
            f"Success is within reach, **{username}**!",
            f"Never stop trying, **{username}**!",
            f"Keep your head up, **{username}**!",
            f"Stay positive and keep moving forward, **{username}**!",
            f"You're on the path to greatness, **{username}**!",
            f"You have what it takes to succeed, **{username}**!",
            f"Believe in yourself and your abilities, **{username}**!",
            f"Stay motivated and keep working hard, **{username}**!",
            f"Your hard work will pay off, **{username}**!",
            f"Never give up on your dreams, **{username}**!",
            f"Stay committed and you will achieve your goals, **{username}**!",
            f"Your perseverance will lead to success, **{username}**!",
            f"Stay driven and determined, **{username}**!",
            f"You're an inspiration, **{username}**!",
            f"Keep pushing through the challenges, **{username}**!",
            f"Success is a journey, not a destination, **{username}**!",
            f"Your dedication is admirable, **{username}**!",
            f"Stay motivated and you will overcome any obstacle, **{username}**!",
            f"Believe in yourself and you can achieve anything, **{username}**!",
            f"You're capable of achieving greatness, **{username}**!",
            f"Keep chasing your dreams, **{username}**!",
            f"You have the strength and determination to succeed, **{username}**!",
            f"Stay focused on your goals, **{username}**!",
            f"Your hard work and determination will pay off, **{username}**!",
            f"Believe you can and you're halfway there, **{username}**.",
            f"The only way to do great work is to love what you do, **{username}**.",
            f"Believe in yourself, take on your challenges, dig deep within yourself to conquer fears. Never let anyone bring you down, **{username}**.",
            f"If you can dream it, you can achieve it, **{username}**.",
            f"Success is not final, failure is not fatal: it is the courage to continue that counts, **{username}**.",
            f"Believe in your potential and you will go far, **{username}**.",
            f"Every great story begins with a hero, and you are the hero of your story, **{username}**.",
            f"The greatest glory in living lies not in never falling, but in rising every time we fall, **{username}**.",
            f"Stay motivated and you will reach your full potential, **{username}**!",
            f"You're an unstoppable force, **{username}**!",
            f"Keep pushing past your limits, **{username}**!",
            f"Stay positive and you will achieve greatness, **{username}**!",
            f"Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle, **{username}**.",
            f"Don't watch the clock; do what it does. Keep going, **{username}**.",
            f"You can't go back and change the beginning, but you can start where you are and change the ending, **{username}**.",
            f"The secret of getting ahead is getting started, **{username}**.",
            f"You are never too old to set another goal or to dream a new dream, **{username}**.",
            f"I can't change the direction of the wind, but I can adjust my sails to always reach my destination, **{username}**.",
            f"It does not matter how slowly you go as long as you do not stop, **{username}**.",
            f"Start where you are. Use what you have. Do what you can, **{username}**.",
            f"Believe in yourself and you will be unstoppable, **{username}**.",
            f"The only way to do great work is to love what you do, **{username}**.",
            f"Don't let yesterday take up too much of today, **{username}**.",
            f"**{username}**, you are not a product of circumstances; you are a product of decisions.",
            f"Believe in yourself and all that you are. Know that there is something inside you that is greater than any obstacle, **{username}**.",
            f"The best way to predict your future is to create it, **{username}**.",
            f"Don't be pushed around by the fears in your mind. Be led by the dreams in your heart, **{username}**.",
            f"The way to get started is to quit talking and begin doing, **{username}**.",
            f"**{username}**, all the great performers I have worked with are fueled by a personal dream.",
            f"**{username}**, time stays long enough for anyone who will use it.",
            f"**{username}**, setting an example is not the main means of influencing another, it is the only means."
        ]
    await context.send(random.choice(messages))

bot.run(os.getenv("TOKEN"))

