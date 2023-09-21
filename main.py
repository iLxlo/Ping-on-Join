import asyncio
import discord
from discord.ext import commands
import tracemalloc

tracemalloc.start()

intents = discord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True
client = commands.AutoShardedBot(command_prefix="*", intents=intents)

guild_channels = {}
new_members = {}


@client.event
async def on_member_join(member):
  guild_id = member.guild.id
  if guild_id not in new_members:
    new_members[guild_id] = []
  new_members[guild_id].append(member)


async def get_channel(guild, channel_id):
  channel = guild.get_channel(channel_id)
  if channel is None:
    channel = guild.text_channels[0]
  return channel


async def get_welcome_channel(guild, channel_name):
  if guild.id in guild_channels and channel_name in guild_channels[guild.id]:
    channel_id = guild_channels[guild.id][channel_name]
    channel = await get_channel(guild, channel_id)
  else:
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    if channel is None:
      channel = guild.text_channels[0]
    guild_channels.setdefault(guild.id, {})[channel_name] = channel.id
  return channel


async def delete_bot_messages(channel):
  messages = []
  async for message in channel.history(limit=100):
    if message.author == client.user:
      messages.append(message)

  if len(messages) > 0:
    await channel.delete_messages(messages)


async def send_message():
  while True:
    for guild_id in list(new_members.keys()):
      guild = client.get_guild(guild_id)
      for channel_name in guild_channels.get(guild_id, []):
        member_list = new_members.get(guild_id, [])
        if len(member_list) > 0:
          channel = await get_welcome_channel(guild, channel_name)
          if len(member_list) <= 10:
            await channel.send(
              f'{", ".join([member.mention for member in member_list])}')
          else:
            message = ''
            for i in range(0, len(member_list), 10):
              message += f'{", ".join([member.mention for member in member_list[i:i+10]])}\n'
            await channel.send(message)
          await delete_bot_messages(
            channel
          )  # Move the call to delete_bot_messages inside the for loop
      new_members[guild_id] = []
    await asyncio.sleep(2)


@client.command()
async def poj(ctx, channel_name=None):
  if channel_name is None:
    channel = ctx.message.channel
  else:
    channel = discord.utils.get(ctx.guild.channels, mention=channel_name)
    if channel is None:
      channel = discord.utils.get(ctx.guild.text_channels, name=channel_name)
    if channel is None:
      await ctx.send('Invalid channel name or mention.')
      return

  guild_id = ctx.guild.id
  guild_channels.setdefault(guild_id, {})
  if channel.id in guild_channels[guild_id].values():
    channel_name = list(guild_channels[guild_id].keys())[list(
      guild_channels[guild_id].values()).index(channel.id)]
    del guild_channels[guild_id][channel_name]
    await ctx.send(f'POJ messages will no longer be sent to {channel.mention}.'
                   )
  else:
    guild_channels[guild_id][channel.name] = channel.id
    await ctx.send(f'POJ messages will now be sent to {channel.mention}.')


@poj.error
async def poj_error(ctx, error):
  if isinstance(error, commands.errors.MissingRequiredArgument):
    await ctx.send('Please specify a channel name.')
  elif isinstance(error, commands.errors.ChannelNotFound):
    await ctx.send('Invalid channel name.')
  else:
    await ctx.send(f'An error occurred: {error}')


@client.command()
async def poj_list(ctx):
  if ctx.guild.id not in guild_channels:
    await ctx.send(f'No channels are set up for POJ messages.')
  else:
    channels_mention = []
    for channel_name in guild_channels[ctx.guild.id]:
      channel_id = guild_channels[ctx.guild.id][channel_name]
      channel = await get_channel(ctx.guild, channel_id)
      channels_mention.append(channel.mention)
    channel_list = '\n'.join(channels_mention)
    await ctx.send(f'Channels set up for POJ messages:\n{channel_list}')


@client.event
async def on_ready():
  print(f'Logged in as {client.user}')
  client.loop.create_task(send_message())


client.run(
  'MTA3Mzk4Mzg0NzkwNzIxNzQ2OQ.GwgTsZ.wSxnK3HzwfrJSoYz9dPPEKttgR4FG7f3JiBjfo')
