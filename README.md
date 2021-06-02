# brdybot
This is a bot adapted from [chatbot-python-sample](https://github.com/twitchdev/chatbot-python-sample) that I use for my Twitch channel, [twitch.tv/brdy](https://www.twitch.tv/brdy).

The bot uses a PostgreSQL database with data scraped and taken from [Serebii.net](https://www.serebii.net), [Bulbapedia](https://bulbapedia.net), [veekun](https://github.com/veekun/pokedex), [Smogon University](https://www.smogon.com), and [pokemondb.net](https://pokemondb.net/).

![image](screens/chatbotshot.png)

# Bot
The bot has the following commands available:
- !game <game abbreviation>: Sets the game and generation using an abbreviation code.
  
 ![image](screens/game.PNG) 
 ![image](screens/game2.PNG)
  
- !move <move name>: Looks up a move name and returns all generation-specific information about the move in the chat (name, pp, power, accuracy, category, contact/no contact, summary of effects,etc.).
  
 ![image](screens/move.PNG)
 ![image](screens/move2.PNG)
  
- !mon <pokemon name>: Looks up a pokemon and returns all game-specific information about the pokemon in the chat (dex, name, type, BST, xp yield, evolution(s), learnset).
  
 ![image](screens/mon.PNG)
 ![image](screens/mon2.PNG) 
  
- !nature <nature>: Looks up a nature name and returns the affected stats in the chat.
  
 ![image](screens/nature.PNG) 
  
- !ability <ability name>: Looks up an ability and returns a generation-specific summary of the ability with a description of its effects in the chat.
  
 ![image](screens/ability2.PNG) 
 ![image](screens/ability.PNG) 

# Data
The database is not available in this repo, but the table schema is as follows:

"pokemon"	"ability"

"pokemon"	"egggroup"

"pokemon"	"evolutiontype"

"pokemon"	"game"

"pokemon"	"gamegroup"

"pokemon"	"generation"

"pokemon"	"generationability"

"pokemon"	"item"

"pokemon"	"itemgeneration"

"pokemon"	"itemtype"

"pokemon"	"levelingrate"

"pokemon"	"levelingrateequation"

"pokemon"	"location"

"pokemon"	"move"

"pokemon"	"movecategory"

"pokemon"	"nature"

"pokemon"	"pokemon"

"pokemon"	"pokemonability"

"pokemon"	"pokemonegggroup"

"pokemon"	"pokemonevolution"

"pokemon"	"pokemonevolutionitem"

"pokemon"	"pokemonevolutionlevel"

"pokemon"	"pokemonevolutionlocation"

"pokemon"	"pokemonevolutionmove"

"pokemon"	"pokemonevolutionstring"

"pokemon"	"pokemonexperienceyield"

"pokemon"	"pokemonmove"

"pokemon"	"pokemonmovemethod"

"pokemon"	"pokemonstat"

"pokemon"	"pokemontype"

"pokemon"	"pokemonvariant"

"pokemon"	"pokemonvarianttype"

"pokemon"	"stat"

"pokemon"	"type"
