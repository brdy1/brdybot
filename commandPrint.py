from brdybot import getGameID, getMonInfo, performSQL,getMonID,getMoveID,getMonMoves,dbConfig
from app import *

#get all pokemonids for gen 8
mons = ['Ledian','Galarian Darmanitan','Applin','Giratina','Thwackey','Stoutland','Shedinja','Lanturn','Klang','Porygon','Vileplume','Claydol','Grotle','Galarian Meowth','Volbeat','Throh','Vanillite','Nidoqueen','Togepi','Golbat','Diancie','Barbaracle','Vikavolt','Glameow','Passimian','Fomantis','Kyogre','Charmander','Poliwrath','Munna','Alolan Sandslash','Garchomp','Tirtouga','Articuno','Lunatone','Cranidos','Archeops','Zweilous','Stantler','Surskit','Snorunt','Manectric','Wynaut','Abra','Pumpkaboo (Large)','Roggenrola','Riolu','Banette','Swoobat','Seaking','Silcoon','Charizard','Mimikyu','Chimchar','Sigilyph','Farfetch''d','Porygon2','Galarian Articuno','Emolga','Gossifleur','Spheal','Seviper','Golem','Staryu','Metapod','Venipede','Mightyena','Gengar','Weedle','Dragapult','Tyrantrum','Darmanitan','Tapu Fini','Cacturne','Goomy','Bagon','Lapras','Golduck','Rowlet','Carbink','Kyurem (Black)','Nidorina','Kecleon','Gliscor','Taillow','Krookodile','Vigoroth','Galarian Zigzagoon','Electivire','Vullaby','Cosmog','Bounsweet','Eternatus','Galarian Farfetch''d','Pumpkaboo (Super)','Doublade','Woobat','Toxapex','Machop','Machamp','Coalossal','Galarian Moltres','Celebi','Elgyem','Deoxys (Speed Form)','Mamoswine','Zamazenta (Crowned Shield)','Hoothoot','Alolan Meowth','Giratina (Origin Form)','Kabuto','Poipole','Thundurus-T','Spinda','Makuhita','Toxtricity (Amped Form)','Totodile','Gligar','Eldegoss','Indeedee-M','Budew','Walrein','Murkrow','Scorbunny','Alolan Dugtrio','Clefairy','Chewtle','Trubbish','Ursaring','Grimmsnarl','Infernape','Spiritomb','Sandslash','Swirlix','Manaphy','Yamper','Togekiss','Cubone','Kadabra','Charjabug','Honedge','Deoxys (Defense Form)','Sliggoo','Poliwag','Nuzleaf','Corsola','Entei','Registeel','Rillaboom','Tapu Koko','Gardevoir','Alcremie','Sableye','Mewtwo','Aipom','Wormadam (Plant Cloak)','Qwilfish','Sawk','Cascoon','Pichu','Hitmonlee','Lycanroc (Dusk Form)','Marill','Roselia','Galarian Rapidash','Minior (Meteor Form)','Landorus-T','Ralts','Lairon','Gothorita','Oddish','Hatterene','Drilbur','Hitmontop','Shuckle','Hariyama','Drednaw','Whirlipede','Deino','Raboot','Kangaskhan','Linoone','Skiploom','Minun','Meowth','Togedemaru','Combusken','Pincurchin','Petilil','Spearow','Galarian Yamask','Steenee','Rampardos','Tranquill','Electrode','Bayleef','Ninjask','Morpeko','Oranguru','Luvdisc','Tapu Bulu','Wimpod','Bewear','Zeraora','Lurantis','Metagross','Eiscue (Noice Face)','Carracosta','Drifblim','Honchkrow','Jigglypuff','Meltan','Torterra','Meditite','Ampharos','Bouffalant','Slowbro','Milotic','Skarmory','Clobbopus','Drampa','Cleffa','Psyduck','Tornadus-T','Fearow','Omastar','Cyndaquil','Yanma','Persian','Zekrom','Wingull','Zacian','Greedent','Cryogonal','Kricketot','Wishiwashi (School Form)','Araquanid','Larvitar','Urshifu (Rapid Strike)','Regice','Zapdos','Empoleon','Blipbug','Mr. Mime','Arctozolt','Helioptile','Morgrem','Silicobra','Breloom','Eiscue','Mawile','Bergmite','Slakoth','Nidoran-F','Carkol','Unfezant','Cufant','Azumarill','Drizzile','Magmortar','Kubfu','Lycanroc (Midnight Form)','Azurill','Venusaur','Azelf','Frillish','Alolan Exeggutor','Wailmer','Escavalier','Rockruff (Event)','Victini','Piplup','Cresselia','Swellow','Solrock','Lugia','Rapidash','Sharpedo','Tyranitar','Nosepass','Illumise','Chansey','Doduo','Pidove','Clamperl','Electabuzz','Floatzel','Snom','Mareep','Zygarde (50% Form)','Seismitoad','Haxorus','Turtwig','Lopunny','Milcery','Buneary','Miltank','Roserade','Sizzlipede','Noivern','Furret','Wooloo','Alolan Sandshrew','Litten','Burmy','Noctowl','Exeggcute','Mew','Kakuna','Pheromosa','Phanpy','Larvesta','Volcanion','Jolteon','Dewgong','Alolan Ninetales','Lumineon','Bunnelby','Klinklang','Klink','Alakazam','Ariados','Bulbasaur','Beheeyem','Victreebel','Tsareena','Ferrothorn','Pelipper','Heracross','Trapinch','Starly','Glalie','Vibrava','Skorupi','Wailord','Chingling','Archen','Rayquaza','Drakloak','Mienfoo','Chandelure','Hippopotas','Bellsprout','Mr. Rime','Koffing','Amaura','Sceptile','Slaking','Clauncher','Carnivine','Clawitzer','Typhlosion','Lillipup','Raichu','Castform (Rainy Form)','Paras','Ekans','Blacephalon','Lunala','Lilligant','Magnemite','Hatenna','Scraggy','Wormadam (Sandy Cloak)','Shaymin (Sky Form)','Relicanth','Chinchou','Mow Rotom','Quagsire','Venomoth','Dracovish','Swablu','Sudowoodo','Sneasel','Dragalge','Turtonator','Flaaffy','Primarina','Rhyperior','Castform (Sunny Form)','Primeape','Cloyster','Regigigas','Armaldo','Hitmonchan','Galarian Slowpoke','Phantump','Pumpkaboo (Average)','Jangmo-o','Klefki','Urshifu (Single Strike)','Girafarig','Flygon','Hippowdon','Kartana','Skwovet','Gothitelle','Kyurem (White)','Arctovish','Bidoof','Numel','Bronzong','Yanmega','Magcargo','Joltik','Smeargle','Cinderace','Druddigon','Skrelp','Galarian Mr. Mime','Scrafty','Magearna','Nidoking','Staraptor','Delcatty','Gabite','Ditto','Scolipede','Castform','Galarian Darmanitan (Zen Mode)','Falinks','Igglybuff','Avalugg','Drifloon','Clefable','Espurr','Orbeetle','Alolan Persian','Stakataka','Vulpix','Mandibuzz','Caterpie','Voltorb','Pachirisu','Anorith','Nincada','Heat Rotom','Growlithe','Lickilicky','Whimsicott','Alolan Vulpix','Deoxys','Sentret','Spoink','Cosmoem','Dusclops','Sylveon','Dottler','Spectrier','Barboach','Dugtrio','Sealeo','Stunky','Dratini','Rhyhorn','Finneon','Dhelmise','Squirtle','Timburr','Vespiquen','Pinsir','Barraskewda','Incineroar','Litwick','Duosion','Palkia','Impidimp','Electrike','Drapion','Cubchoo','Houndoom','Slugma','Mantyke','Talonflame','Tentacool','Binacle','Remoraid','Hattrem','Mankey','Zygarde (10% Form)','Pawniard','Arbok','Galvantula','Alolan Marowak','Quilava','Sobble','Morelull','Yveltal','Luxio','Masquerain','Beedrill','Crustle','Crobat','Gothita','Croagunk','Calyrex (Ice Rider)','Gulpin','Dedenne','Galarian Corsola','Probopass','Rolycoly','Luxray','Aggron','Snorlax','Graveler','Reshiram','Steelix','Umbreon','Groudon','Butterfree','Raticate','Necrozma (Dawn Wings)','Volcarona','Forretress','Dunsparce','Phione','Shellos','Centiskorch','Golett','Silvally','Corvisquire','Conkeldurr','Moltres','Kricketune','Latios','Spritzee','Scizor','Golurk','Pangoro','Mudbray','Snubbull','Grapploct','Kabutops','Ninetales','Zarude','Scyther','Hoppip','Cobalion','Fan Rotom','Swinub','Dragonair','Torkoal','Solosis','Goldeen','Dialga','Runerigus','Heatran','Buizel','Granbull','Gourgeist (Super)','Arceus','Heliolisk','Arcanine','Axew','Lotad','Gourgeist (Small)','Stunfisk','Meganium','Galarian Darumaka','Diggersby','Octillery','Pidgeot','Excadrill','Boltund','Seadra','Shaymin','Combee','Plusle','Shinx','Gastly','Shieldon','Comfey','Inkay','Gallade','Seel','Cradily','Grovyle','Purrloin','Gible','Landorus','Leafeon','Baltoy','Dreepy','Duskull','Drowzee','Whiscash','Venonat','Dracozolt','Aegislash (Shield Form)','Minccino','Musharna','Mismagius','Kingdra','Regidrago','Tornadus','Spinarak','Celesteela','Salamence','Froslass','Aron','Basculin','Darmanitan (Zen Mode)','Dwebble','Croconaw','Shuppet','Grookey','Melmetal','Necrozma','Type: Null','Mothim','Cursola','Aurorus','Ho-Oh','Golisopod','Rockruff','Zubat','Shelgon','Munchlax','Swalot','Donphan','Beautifly','Uxie','Guzzlord','Marshtomp','Blaziken','Galarian Weezing','Chikorita','Slowpoke','Lycanroc (Midday Form)','Snover','Thundurus','Gurdurr','Lickitung','Latias','Espeon','Rufflet','Pineco','Charmeleon','Bisharp','Gigalith','Polteageist','Galarian Zapdos','Kyurem','Whismur','Indeedee-F','Amoonguss','Haunter','Stufful','Xurkitree','Vanilluxe','Hydreigon','Zigzagoon','Liepard','Tyrunt','Arrokuda','Shiftry','Poochyena','Nidorino','Wormadam (Trash Cloak)','Xerneas','Huntail','Decidueye','Ponyta','Machoke','Ribombee','Regieleki','Jumpluff','Alolan Raichu','Magneton','Shiinotic','Eevee','Mantine','Cramorant','Onix','Omanyte','Torracat','Meowstic-M','Muk','Trevenant','Treecko','Zamazenta','Nihilego','Rhydon','Durant','Bronzor','Gloom','Chatot','Dartrix','Galarian Slowbro','Toxicroak','Sunflora','Fletchinder','Marshadow','Skitty','Galarian Linoone','Rotom','Metang','Sunkern','Geodude','Popplio','Corviknight','Dustox','Jellicent','Kingler','Audino','Gyarados','Elekid','Sandile','Unown','Sinistea','Terrakion','Alolan Diglett','Glastrier','Bastiodon','Magikarp','Darumaka','Galarian Ponyta','Flapple','Tangrowth','Pyukumuku','Thievul','Darkrai','Gourgeist (Average)','Tympole','Flareon','Glaceon','Ambipom','Ferroseed','Staravia','Brionne','Camerupt','Wash Rotom','Mudsdale','Grumpig','Houndour','Gourgeist (Large)','Cacnea','Yamask','Dusknoir','Mareanie','Shroomish','Weezing','Tapu Lele','Dragonite','Ivysaur','Noibat','Poliwhirl','Calyrex','Salazzle','Cherrim','Vaporeon','Cinccino','Herdier','Rattata','Beldum','Perrserker','Seedot','Porygon-Z','Misdreavus','Genesect','Buzzwole','Zorua','Medicham','Lombre','Tauros','Wishiwashi (Solo Form)','Sandaconda','Gastrodon','Weavile','Exeggutor','Hakamo-o','Reuniclus','Pumpkaboo (Small)','Karrablast','Purugly','Altaria','Boldore','Kommo-o','Pancham','Sandshrew','Lampent','Monferno','Grimer','Shelmet','Swampert','Malamar','Smoochum','Toxel','Garbodor','Bonsly','Toxtricity (Low Key Form)','Stonjourner','Kirlia','Wobbuffet','Abomasnow','Tropius','Deoxys (Attack Form)','Pidgey','Pidgeotto','Maractus','Mime Jr.','Hawlucha','Aegislash (Blade Form)','Fraxure','Castform (Snowy Form)','Aerodactyl','Solgaleo','Necrozma (Ultra Necrozma)','Corphish','Frosmoth','Wigglytuff','Chimecho','Shellder','Rookidee','Starmie','Regirock','Loudred','Feebas','Dodrio','Lucario','Vanillish','Prinplup','Braviary','Beartic','Magnezone','Carvanha','Sirfetch''d','Bibarel','Sandygast','Horsea','Naganadel','Parasect','Blastoise','Feraligatr','Wooper','Crawdaunt','Zygarde (Complete Form)','Natu','Cofagrigus','Aromatisse','Fletchling','Gorebyss','Lileep','Palossand','Mienshao','Absol','Accelgor','Mesprit','Togetic','Frost Rotom','Slurpuff','Nickit','Foongus','Bellossom','Zangoose','Ledyba','Necrozma (Dusk Mane)','Marowak','Krabby','Inteleon',
'Cottonee','Politoed','Exploud','Jirachi','Meowstic-F','Palpitoad','Zoroark','Cherubi','Calyrex (Shadow Rider)','Dubwool','Cutiefly','Galarian Stunfisk','Diglett','Grubbin','Nidoran-M','Raikou','Minior (Core Form)','Salandit','Tyrogue','Piloswine','Eternamax Eternatus','Zacian (Crowned Sword)','Galarian Slowking','Pikachu','Suicune','Heatmor','Skuntank','Virizion','Slowking','Teddiursa','Blissey','Magby','Keldeo','Copperajah','Mudkip','Delibird','Jynx','Tangela','Krokorok','Torchic','Appletun','Obstagoon','Dewpider','Pupitar','Xatu','Weepinbell','Happiny','Magmar','Goodra','Wartortle','Hypno','Tentacruel','Wurmple','Ludicolo','Duraludon']

for monName in mons:
    monid,monName = getMonID(monName,'brdy')
    if monid:
        moves = getMonMoves(str(monid),True,'brdy') 
        print(str(moves))
        input()

    # sql = "SELECT game.gamegroupid,gamegroup.gamegroupname FROM pokemon.gamegroup LEFT JOIN pokemon.game ON gamegroup.gamegroupid = game.gamegroupid WHERE gamename = '"+game+"'"
    # gamegroupID = performSQL(sql)[0][0]
    # pokemonName = input("Pokemon Name:\r\n")
    