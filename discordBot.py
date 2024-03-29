import os
import nextcord
from nextcord.ext import commands
import requests
import base64
from dotenv import dotenv_values
import json

config = {
    **os.environ,
    **dotenv_values(".env")
}

class Printer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.canPrint = True
        self.canPlaySound = True

    @commands.command(name="toggle_print")
    async def toggle_print(self, ctx: commands.Context):
        if(self.admin_check(ctx.author.id)):
            self.canPrint = not self.canPrint
            await ctx.send(f'printing feature toggled {"on" if self.canPrint else "off"}')
        else: 
            await ctx.send("Sorry but you are not authorized to use this command")
    
    @commands.command(name="toggle_sound")
    async def toggle_sound(self, ctx: commands.Context):
        if(self.admin_check(ctx.author.id)):
            self.canPlaySound = not self.canPlaySound
            await ctx.send(f'sound playing feature toggled {"on" if self.canPlaySound else "off"}')
        else: 
            await ctx.send("Sorry but you are not authorized to use this command")
    
    def admin_check(self, authorId: int):
        return any(authorId == id for id in json.loads(config.get("ADMIN_ID")))  

    @commands.Cog.listener()
    async def on_command_error(self, _, error: commands.CommandError):
        if isinstance(error, commands.CommandNotFound):
            return
        raise error

    @nextcord.slash_command(name="print_image", description="print an image")
    async def print_image(self, inter:nextcord.Interaction, image: nextcord.Attachment = nextcord.SlashOption(name="image", description="image to print", required=True)):
        if(self.canPrint):
            if(image.content_type.startswith("image/")):
                await inter.send("Image received. Start printing")
                responseimage = requests.get(image.url)
                if(responseimage.status_code == 200):
                    if(self.canPrint):
                        encodedImage = base64.b64encode(s=responseimage.content).decode("utf-8")
                        await self.printer_print(inter= inter, text=encodedImage, type="image")
                    else: 
                        await inter.edit_original_message(content="Sorry the printing service is not available. Please try again later")
                else:
                    await inter.edit_original_message(content="Something went wrong receiving your image. Please try again")
            else:
                await inter.send("That's not an image. Please send an image")
        else: 
            await self.send_not_available(inter)

    @nextcord.slash_command(name="print_message",  description="Print a text message", )
    async def print_message(self, inter: nextcord.Interaction, message: str = nextcord.SlashOption(name="message", description="text to print")): 
        if(self.canPrint):
            # if(self.isReady()):
                await inter.send(f"printing")
                await self.printer_print(inter=inter, text=message, type="text")
            # else: 
            #     await inter.response.send_message("printer currently not ready")
        else: 
            await self.send_not_available(inter=inter)

    async def printer_print(self, inter:nextcord.Interaction, text:str, type: str):
        body = {
        "author":f"{inter.user.display_name}",
        "origin": inter.channel.name if not isinstance(inter.channel, nextcord.channel.PartialMessageable) else "Discord",
        "content": [
                {
                    "data": text,
                    "type": type
                }
            ]
        }
        printResponse = requests.post(f"{config.get('API_URL')}{config.get('PRINT_ENDPOINT')}", json=body)
        if(printResponse.status_code == 200):
            try:
                if(self.canPlaySound):
                    requests.post(f"{config.get('SOUND_URL')}")
            except:
                print("an error occured making the request. This is not the same as a bad response.")
            
            await inter.edit_original_message(content="Printed sucessfully")
        else: 
            print(printResponse.content)
            await inter.edit_original_message(content='Something went wrong')

    async def send_not_available(self, inter: nextcord.Interaction):
        await inter.send("Sorry this feature is currently not available. Please try again later")

    def isReady(self):
        response = requests.get(f"{config.get('API_URL')}{config.get('READCHECK_ENDPOINT')}")
        if(response.status_code == 200):
            return response.json()["ready"]
        else: 
            return False


bot = commands.Bot(command_prefix="/")
bot.add_cog(Printer(bot))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    raise error

@bot.event
async def on_ready():
    print("starting")


bot.run(config.get("DISCORD_TOKEN"))
