import discord
from discord.ext import commands
import sys
import asyncio

# Force l'affichage immédiat des prints
sys.stdout.flush()

# ===== CONFIGURATION =====
MESSAGE_ID = 1437068922057785475  # ⚠️ ID du message (récupéré depuis setup.py)
CHANNEL_ID = 1437062229856882818  # ⚠️ ID du channel (récupéré depuis setup.py)
CATEGORY_ID = 1437062110017359873  # 📌 OPTIONNEL : ID de la catégorie où créer les tickets (None = pas de catégorie)

STAFF_ROLE_IDS = [1437068002943176704, 1437176877474119851]  # 📌 OPTIONNEL : ID du rôle staff qui peut voir les tickets (None = tout le monde)

# ===== BOT SETUP =====
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Stockage en mémoire des tickets ouverts
active_tickets = {}  # {channel_id: user_id}

# ===== CLASSE POUR LE BOUTON DE FERMETURE (persistant) =====
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🔒 Fermer le Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await close_ticket_callback(interaction)

# ===== ÉVÉNEMENTS =====
@bot.event
async def on_ready():
    print(f"✅ Bot connecté : {bot.user}", flush=True)
    
    # Attendre un peu pour que le bot soit complètement prêt
    await asyncio.sleep(2)
    
    # Récupère le message et reconstruit les boutons
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f"❌ Channel {CHANNEL_ID} introuvable !", flush=True)
            print(f"💡 Vérifie que le CHANNEL_ID est correct dans bot.py", flush=True)
            return
            
        print(f"✅ Channel trouvé : {channel.name}", flush=True)
        
        message = await channel.fetch_message(MESSAGE_ID)
        print(f"✅ Message trouvé : {message.id}", flush=True)
        
        # Recrée la vue avec les boutons
        view = TicketView()
        await message.edit(view=view)
        print("✅ Boutons rattachés au message !", flush=True)
        
    except discord.NotFound:
        print(f"❌ Message {MESSAGE_ID} introuvable dans le channel !", flush=True)
        print(f"💡 Vérifie que le MESSAGE_ID est correct dans bot.py", flush=True)
    except discord.Forbidden:
        print(f"❌ Pas les permissions pour accéder au message !", flush=True)
        print(f"💡 Vérifie les permissions du bot sur le serveur", flush=True)
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du message : {e}", flush=True)
    
    # Scanne les tickets existants au démarrage
    await scan_existing_tickets()
    print(f"📊 {len(active_tickets)} ticket(s) actif(s) trouvé(s)", flush=True)

async def scan_existing_tickets():
    """Scanne tous les channels pour retrouver les tickets ouverts et réattacher les boutons"""
    for guild in bot.guilds:
        for channel in guild.text_channels:
            # Vérifie si le nom du channel correspond à un ticket
            if channel.name.startswith(("ticket-", "tech-", "demande-")):
                try:
                    # Récupère la partie après le tiret
                    user_part = channel.name.split("-", 1)[1]
                    active_tickets[channel.id] = user_part  # On garde le pseudo ici
                    print(f"🔍 Ticket trouvé : {channel.name} (User: {user_part})", flush=True)

                    # Réattache le bouton de fermeture
                    async for message in channel.history(limit=10):
                        if message.author == bot.user and len(message.embeds) > 0:
                            await message.edit(view=CloseTicketView())
                            print(f"✅ Bouton de fermeture réattaché pour : {channel.name}", flush=True)
                            break

                except Exception as e:
                    print(f"⚠️ Erreur lors du scan de {channel.name} : {e}", flush=True)

# ===== VUE DES BOUTONS =====
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Recrutement", style=discord.ButtonStyle.success, custom_id="ticket_recrutement")
    async def recrutement_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_ticket(interaction, "Recrutement")
    
    @discord.ui.button(label="Renseignement", style=discord.ButtonStyle.danger, custom_id="ticket_renseignement")
    async def renseignement_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_ticket(interaction, "Renseignement")
    
    @discord.ui.button(label="Autre Demande", style=discord.ButtonStyle.primary, custom_id="ticket_autre")
    async def autre_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_ticket(interaction, "Autre Demande")

# ===== CRÉATION DE TICKET =====
async def create_ticket(interaction: discord.Interaction, ticket_type: str):
    """Crée un nouveau ticket"""
    user = interaction.user
    guild = interaction.guild
    
    print(f"🎫 Demande de ticket : {ticket_type} par {user.name}", flush=True)
    
    # Vérifie si l'utilisateur a déjà un ticket ouvert
    for channel_id, user_id in active_tickets.items():
        if user_id == user.id:
            channel = guild.get_channel(channel_id)
            if channel:
                await interaction.response.send_message(
                    f"❌ Tu as déjà un ticket ouvert : {channel.mention}",
                    ephemeral=True
                )
                print(f"⚠️ {user.name} a déjà un ticket ouvert : {channel.name}", flush=True)
                return
    
    # Nom du channel selon le type de ticket
    channel_names = {
        "Recrutement": f"ticket-{user.name}",
        "Renseignement": f"tech-{user.name}",
        "Autre Demande": f"demande-{user.name}"
    }
    
    channel_name = channel_names.get(ticket_type, f"ticket-{user.name}")
    
    # Permissions du channel
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    # 🔧 CORRECTION : Boucle correctement indentée pour les rôles staff
    for role_id in STAFF_ROLE_IDS:
        staff_role = guild.get_role(role_id)
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    
    # Récupère la catégorie si configurée
    category = guild.get_channel(CATEGORY_ID) if CATEGORY_ID else None
    
    # Crée le channel
    try:
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category,
            topic=f"Ticket de {user.name} ({user.id})"
        )
        
        # Stocke le ticket
        active_tickets[ticket_channel.id] = user.id
        
        # 🔧 CORRECTION : Prépare les mentions des rôles staff
        staff_mentions = []
        for role_id in STAFF_ROLE_IDS:
            staff_role = guild.get_role(role_id)
            if staff_role:
                staff_mentions.append(staff_role.mention)
        
        # ===== MESSAGE DANS LE TICKET =====
        embed = discord.Embed(
            title="🎫 Ticket Ouvert",
            description=f"Bonjour {user.mention} !\n\n"
                        f"Merci d'avoir ouvert un ticket.\n"
                        f"Un membre du staff va te répondre rapidement.\n\n"
                        f"**Type de ticket :** {ticket_type}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Clique sur le bouton ci-dessous pour fermer le ticket")
        # ===== FIN MESSAGE =====
        
        # 🔧 CORRECTION : Utilise la vue persistante
        close_view = CloseTicketView()
        
        # 🔧 CORRECTION : Envoie le ping des staff AU-DESSUS de l'embed
        staff_ping_text = " ".join(staff_mentions) if staff_mentions else ""
        await ticket_channel.send(content=staff_ping_text, embed=embed, view=close_view)
        
        # Répond à l'interaction
        await interaction.response.send_message(
            f"✅ Ton ticket a été créé : {ticket_channel.mention}",
            ephemeral=True
        )
        
        print(f"✅ Ticket créé : {channel_name} pour {user.name}", flush=True)
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Erreur lors de la création du ticket : {e}",
            ephemeral=True
        )
        print(f"❌ Erreur création ticket : {e}", flush=True)

# ===== FERMETURE DE TICKET =====
async def close_ticket_callback(interaction: discord.Interaction):
    """Ferme un ticket"""
    channel = interaction.channel
    
    # Vérifie si c'est bien un ticket
    if channel.id not in active_tickets:
        await interaction.response.send_message(
            "❌ Ce n'est pas un ticket valide !",
            ephemeral=True
        )
        return
    
    # Supprime de la mémoire
    user_id = active_tickets.pop(channel.id)
    
    # Message de confirmation
    await interaction.response.send_message(
        "🔒 Ce ticket va être fermé dans 3 secondes...",
        ephemeral=False
    )
    
    print(f"🔒 Fermeture du ticket : {channel.name} (User: {user_id})", flush=True)
    
    # Attend 3 secondes puis supprime le channel
    await asyncio.sleep(3)
    
    try:
        await channel.delete(reason=f"Ticket fermé par {interaction.user.name}")
        print(f"✅ Ticket supprimé : {channel.name}", flush=True)
    except Exception as e:
        print(f"❌ Erreur lors de la suppression du ticket : {e}", flush=True)

# ===== FONCTION POUR MAIN.PY =====
async def start_bot(token):
    """Fonction appelée par main.py pour démarrer le bot"""
    try:
        print("🔌 Démarrage du bot Discord...", flush=True)
        await bot.start(token)
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du bot : {e}", flush=True)
        raise
