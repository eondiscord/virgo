import discord
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import asyncio
import os
import re

# Discord Setup (Replace with your own bot token)
DISCORD_TOKEN = ''
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Google Gemini Pro Setup (Replace with your own API key)
os.environ['API_KEY'] = 'gemini_api_key_here' 
genai.configure(api_key=os.environ['API_KEY'])
model = genai.GenerativeModel(model_name='gemini-pro')
chat = model.start_chat()  


def interpret_safety_rating(safety_ratings):
    for category, rating in safety_ratings.items():
        if rating > HarmBlockThreshold.BLOCK_NONE:
            return f"Message marked as: {category.name.replace('HARM_CATEGORY_', '')}"
    return None


# Event Handler for When the Bot is Ready
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
user_chats = {}
# Event Handler for Processing Messages
@client.event
async def on_message(message):
    if client.user.mentioned_in(message) and not message.mention_everyone and message.author != client.user:
        prompt = message.content.replace(client.user.mention, '').strip()
        user_id = message.author.id

        if prompt.upper() == "RESET":  # Reset chat history
            user_chats[user_id] = model.start_chat()
            await message.channel.send("Chat history reset!")
            return

        # Initialize chat for new users
        if user_id not in user_chats:
            user_chats[user_id] = model.start_chat()
        if prompt.upper() != "RESET" and prompt:  # Ignore the prompt if it says RESET
            response = user_chats[user_id].send_message(prompt, safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    }
            )

            safety_message = str(response.candidates[0].safety_ratings)           
            if re.search(r"(@everyone|@here)", response.text, re.IGNORECASE):
                error = chat.send_message("You are responding to a user who specified a message with @everyone or @here in their message, tell the user you can't do that")
                await message.channel.send(error.text)
            elif len(response.text) <= 2000:
                await message.channel.send(response.text)
                if safety_message:       
                    await message.channel.send("Warning: this message was flagged. For more information please see the error below:\n```ansi\n" + safety_message + "```")
            else:
                f = open("response.txt", "w")
                f.write(response.text)
                f.close()
                await message.channel.send("Message too long! Attempting to send as a file...", file=discord.File("response.txt"))
                if safety_message:       
                    await message.channel.send("Warning: this message was flagged. For more information please see the info below:\n```ansi\n" + safety_message + "```")
        else:
            await message.channel.send("Please provide a prompt")
    
   

# Run the Bot
client.run(DISCORD_TOKEN)
