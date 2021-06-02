# brdybot
This is a bot adapted from [chatbot-python-sample](https://github.com/twitchdev/chatbot-python-sample) that I use for my Twitch channel, [twitch.tv/brdy](https://www.twitch.tv/brdy).

The bot uses a PostgreSQL database with data scraped and taken from [Serebii.net](https://www.serebii.net), [Bulbapedia](https://bulbapedia.net), [veekun](https://github.com/veekun/pokedex), [Smogon University](https://www.smogon.com), and [pokemondb.net](https://pokemondb.net/).

# Bot
The bot has the following commands available:
- !game <game abbreviation>: Sets the game and generation using an abbreviation code.
  - !game DP
- !move <move name>: Looks up a move name and returns all information about the move in the chat (name, pp, power, accuracy, contact/no contact, summary of effects).
  - !move acid
- !mon <pokemon name>: Looks up a pokemon and returns all information about the pokemon in the chat (dex, name, BST, xp yield, evolution(s), learnset).
  - !mon charizard
- !nature <nature>: Looks up a nature name and returns the affected stats in the chat.
  - !nature docile
- !ability <ability name>: Looks up an ability and returns a summary of the ability with the actual effects in the chat.
  - !ability lightning rod

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
