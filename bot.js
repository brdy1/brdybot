

const tmi = require('tmi.js');

// Define configuration options
const opts = {
  identity: {
    username: "brdybot",
    password: "b0dmrp1p5k6n2agsmz224lp47unrvj"
  },
  channels: [
    "brdy"
  ]
};

// Create a client with our options
const client = new tmi.client(opts);

// Register our event handlers (defined below)
client.on('message', onMessageHandler);
client.on('connected', onConnectedHandler);

// Connect to Twitch:
client.connect();

// Called every time a message comes in
function onMessageHandler (target, context, msg, self) {
  if (self) { return; } // Ignore messages from the bot

  // Remove whitespace from chat message
  const commandName = msg.trim();

  // If the command is known, let's execute it
  if (commandName === '!challenges') {
    client.say(target, 'brdy is challenging himself to complete games, challenge runs, and other achievements. See the spreadsheet here for status: https://docs.google.com/spreadsheets/d/1BcEslzyAT4H6ZI7W6cwlGfYPCAB-0db-wxclFoO2B78/edit?usp=sharing');
    logCommand(commandName);
  }

  else if (commandName === '!discord') {
      client.say(target, 'brdy Discord: https://discord.gg/PGfsbsc384');
      logCommand(commandName);
  }
  
  else if (commandName === '!evolutions') {
      client.say(target, 'Any pokemon that requires trading or other unlikely conditions to evolve will evolve by leveling up just like any other pokemon. Pokemon that require held items will still require them, but will evolve by leveling instead of trading if it is required.');
      logCommand(commandName);
  }

  else if (commandName === '!favorites') {
      client.say(target, 'Gen 4: Mamoswine, Electivire, Suicune');
      logCommand(commandName);
  }

  else if (commandName === '!ironmon') {
      client.say(target, "In this Pokemon challenge run conceived of by iateyourpie, starters are randomized, all wild Pokemon are random, and all trainers and gym leaders have randomized pokemon with a +50% level increase. All Pokemon will have randomized movesets and learnsets (including the ability to learn TMs). I cannot farm wild pokemon for experience. If a Pokemon faints, I have to box it. Pie's pastebin: https://pastebin.com/L48bttfz");
      logCommand(commandName);
  }

  else if (commandName === '!lastrun') {
      client.say(target, "https://clips.twitch.tv/SoftAverageGooseDancingBaby-35lLOsI_PB5_vCtQ");
      logCommand(commandName);
  }

  else if (commandName === '!snes') {
      client.say(target, "As part of his selection of challenges, brdy is completing the whole SNES library. That's 720 games total! \"Completion\" is defined as story mode, career mode, etc. Check out the spreadsheet for completion status on each of the games: https://docs.google.com/spreadsheets/d/1BcEslzyAT4H6ZI7W6cwlGfYPCAB-0db-wxclFoO2B78");
      logCommand(commandName);
  }

  else if (commandName.includes('!pkmn')) {
    // if (mod === 1) {
    // command, pokemon = commandName.split(" ")
    // pokemon = pokemon.trim();
    // fetchPokemon(pokemon);
    // }
    // else {
    //     client.say(target, "The !pkmn command is currently available only to subscribers and mods.")
    // }
    // logCommand(commandName);

    console.log(`*  ${target}, ${context}, ${msg} `);
}
  else {
    console.log(`* Unknown command ${commandName}`);
  }
}

// Function called when the "dice" command is issued
function rollDice () {
  const sides = 6;
  return Math.floor(Math.random() * sides) + 1;
}

// Called every time the bot connects to Twitch chat
function onConnectedHandler (addr, port) {
  console.log(`* Connected to ${addr}:${port}`);
}

// Record a command executed in chat, printed to the console
function logCommand (commandName) {
    console.log(`* Executed ${commandName} command`);
}

function fetchPokemon (pokemonName) {
  const df = new DataFrame()  
  
}