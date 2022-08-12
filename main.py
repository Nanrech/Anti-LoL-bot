import interactions as ipy
from json import load, dump

client = ipy.Client(
    token="",
    presence=ipy.ClientPresence(
        activities=[
            ipy.PresenceActivity(
                type=ipy.PresenceActivityType.WATCHING,
                name="y'all nerds"
            )
        ],
        status=ipy.StatusType.DND
    ),
    disable_sync=False,
    intents=ipy.Intents.DEFAULT | ipy.Intents.GUILD_PRESENCES
)


@client.event
async def on_start():
    print(f"Logged in as {client.me.name}")


def get_log_channel(guild_id: str):
    with open("log_channels.json", "r") as f:
        log_channels = load(f)
    return log_channels.get(guild_id)


def register_log_channel(guild_id: str, channel_id: str):
    with open("log_channels.json", "r") as f:
        log_channels = load(f)
    log_channels[guild_id] = channel_id
    with open("log_channels.json", "w") as f:
        dump(log_channels, f)


def remove_log_channel(guild_id: str):
    with open("log_channels.json", "r") as f:
        log_channels = load(f)
    log_channels.pop(guild_id)
    with open("log_channels.json", "w") as f:
        dump(log_channels, f)


@client.command()
async def logs(ctx: ipy.CommandContext):
    """This description isn't seen in UI (yet?)"""
    pass


@logs.subcommand()
@ipy.option(name="channel",
            description="The log channel",
            required=False)
async def add(ctx: ipy.CommandContext, channel: ipy.Channel = None):
    """Select a channel to send logs into"""
    register_log_channel(guild_id=str(ctx.guild_id), channel_id=str(ctx.channel_id))
    await ctx.send(f"Registered {channel.mention}",
                   ephemeral=True)


@logs.subcommand()
async def remove(ctx: ipy.CommandContext):
    """Removes all logging"""
    if not get_log_channel(str(ctx.guild_id)):
        return await ctx.send("Server didn't have a log channel set",
                              ephemeral=True)
    remove_log_channel(str(ctx.guild_id))
    await ctx.send(f"Removed all logging")


@client.command()
@ipy.option(name="setting",
            description="Choose how the bot will react when detecting a League of Legends player",
            required=True,
            choices=[
                ipy.Choice(name="Lethal mode", value="lethal"),
                ipy.Choice(name="Alert mode", value="alert")
            ])
async def mode(ctx: ipy.CommandContext, setting: str):
    with open("mode.json", "r") as f:
        modejson = load(f)
    modejson[str(ctx.guild_id)] = setting
    with open("mode.json", "w") as f:
        dump(modejson, f)

    if setting.startswith('l'):
        await ctx.send("Bot will now attempt to ban anyone caught playing LoL",
                       ephemeral=True)
    else:
        await ctx.send("Bot will now just send an alert when someone starts playing league of legends",
                       ephemeral=True)


@client.event
async def on_raw_presence_update(payload: ipy.Presence):
    for activity in payload.activities:
        if "Visual" in activity.name:
            with open("mode.json", "r") as f:
                modejson = load(f)
            if modejson.get(str(payload.guild_id)) == "alert" or not modejson.get(str(payload.guild_id)):
                with open("log_channels.json", "r") as f:
                    log_channels = load(f)
                if not log_channels.get(str(payload.guild_id)):
                    return
                await client._http.send_message(channel_id=log_channels.get(payload.guild_id),
                                                content=f"`{payload.user.id}` {payload.user} is playing LoL!")
            else:
                try:
                    await client._http.create_guild_ban(guild_id=int(payload.guild_id),
                                                        user_id=int(payload.user.id))
                except ipy.LibraryException:
                    pass


client.start()
