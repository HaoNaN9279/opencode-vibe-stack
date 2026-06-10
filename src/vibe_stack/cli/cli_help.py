"""Help command — prints CLI usage information."""


def cmd_help(vibe_home=None, project_root=None, **kwargs) -> None:
    """Print the vibe-stack help message."""
    print(
        """
  ╔══════════════════════════════════════════════════════╗
  ║           OpenCode Vibe Stack - CLI Tool             ║
  ╚══════════════════════════════════════════════════════╝

  Manage domain-specific AI agent configurations for your projects.

  USAGE:
    vibe-stack <command> [options]

  COMMANDS:
    list                    List all available domains
    status                  Show active domains in current project
    activate <domain>...    Activate domain(s) in current project
    deactivate <domain>...  Remove domain(s) from current project
    use-stack <name>        Activate all domains from a stack preset
    core-update             Re-sync core symlinks after updating the repo
    help                    Show this help message

  DOMAIN FORMAT:
    <category>/<domain>
    Examples: game-dev/unity, dcc/blender, dcc/maya

  EXAMPLES:
    # List available domains
    vibe-stack list

    # Activate Unity and Blender for current project
    vibe-stack activate game-dev/unity dcc/blender

    # Check what's active
    vibe-stack status

    # Deactivate a domain
    vibe-stack deactivate dcc/blender

    # Use a preset stack
    vibe-stack use-stack game-dev

    # Update core symlinks after git pull
    vibe-stack core-update

  ENVIRONMENT:
    VIBE_STACK_HOME    Override repo location (default: ~/.opencode-vibe-stack)

"""
    )
