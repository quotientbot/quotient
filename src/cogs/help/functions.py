def common_command_formatting(self, embed_like, command):
    embed_like.title = self.get_command_signature(command)
    if command.description:
        embed_like.description = f"{command.description}\n\n{command.help}"
    else:
        embed_like.description = command.help or "No help found..."
        embed_like.add_field(
            name="Aliases",
            value=" | ".join([f"`{alias}`" for alias in command.aliases]) if command.aliases else f"`{command.name}`",
        )
        embed_like.add_field(name="**Usage ** ", value=f"`{self.get_command_signature(command)}`")
