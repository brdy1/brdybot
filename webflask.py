from random import Random
from flask import Flask, request, render_template, session, redirect
import numpy as np
import pandas as pd
import jinja2
from sqlalchemy.orm import Session,aliased
from sqlalchemy import create_engine, func, update, delete, and_, or_, null, case, literal_column
from sqlalchemy.dialects.postgresql import aggregate_order_by, insert
from schema import *
import traceback

loader=jinja2.FileSystemLoader('templates')

app = Flask(__name__)

# df = pd.read_sql("""SELECT
#                         base.pokemonname
#                         ,vanilla.pokemonname
#                         ,target.pokemonname
#                         ,seedcount*(select sum(seedcount) from )
#                     FROM warehouse.randomizerevolutioncountsfull recf
#                         LEFT JOIN pokemon.pokemon base on recf.basepokemonid = base.pokemonid
#                         LEFT JOIN pokemon.pokemon vanilla on recf.vanillatargetid = vanilla.pokemonid
#                         LEFT JOIN pokemon.pokemon target on recf.targetpokemonid = target.pokemonid

#                     WHERE gamegroupid = (
#                         SELECT gamegroupid from pokemon.gamegroup where gamegroupname = 'FireRed/LeafGreen'
#                         )""",engine)

# denominator = session.query(func.sum(RandomizerEvolutionCounts.seedcount)).\
#                         join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
#                         filter(RandomizerEvolutionCounts.basepokemonid == 2,GameGroup.generationid == generation).\
#                         scalar()/100

@app.route('/revotable/<parameters>', methods=("POST", "GET"))
def html_table(parameters):
    try:
        generation,mondex = parameters.split('.')
        session = Session(engine)
        denominator = session.query(func.sum(RandomizerEvolutionCounts.seedcount)).\
                            join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                            filter(RandomizerEvolutionCounts.basepokemonid == 2,GameGroup.generationid == generation).\
                            scalar()/100
        Basemon = aliased(Pokemon)
        Targetmon = aliased(Pokemon)
        Vanillamon = aliased(Pokemon)
        Vanillaevomon = aliased(Pokemon)
        vanillas = session.query(func.count(RandomizerEvolutionCounts.vanillatargetid)).\
                            join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                            join(Basemon,RandomizerEvolutionCounts.basepokemonid == Basemon.pokemonid).\
                            filter(Basemon.pokemonpokedexnumber == mondex,GameGroup.generationid == generation).\
                            scalar()
        if vanillas > 1:
            dfdict = {}
            vanillas = session.query(RandomizerEvolutionCounts.vanillatargetid).\
                            join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                            join(Basemon,RandomizerEvolutionCounts.basepokemonid == Basemon.pokemonid).\
                            filter(Basemon.pokemonpokedexnumber == mondex,GameGroup.generationid == generation).\
                            all()
            dflist = []
            for vanilla in vanillas:
                evoquery = session.query(Basemon.pokemonname,func.coalesce(Vanillamon.pokemonname,Vanillaevomon.pokemonname),Targetmon.pokemonname,(func.sum(RandomizerEvolutionCounts.seedcount))/denominator).\
                                        select_from(RandomizerEvolutionCounts).\
                                        join(Targetmon,RandomizerEvolutionCounts.targetpokemonid == Targetmon.pokemonid).\
                                        join(Basemon,RandomizerEvolutionCounts.basepokemonid == Basemon.pokemonid).\
                                        join(Vanillamon,RandomizerEvolutionCounts.vanillatargetid == Vanillamon.pokemonid,isouter=True).\
                                        join(PokemonEvolutionInfo,(RandomizerEvolutionCounts.basepokemonid == PokemonEvolutionInfo.basepokemonid) & (RandomizerEvolutionCounts.vanillatargetid == None),isouter=True).\
                                        join(Vanillaevomon,PokemonEvolutionInfo.targetpokemonid == Vanillaevomon.pokemonid,isouter=True).\
                                        join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                                        filter((GameGroup.generationid == generation) & (Basemon.pokemonpokedexnumber == mondex) & (Vanillamon.pokemonid == vanilla)).\
                                        group_by(Basemon.pokemonname,func.coalesce(Vanillamon.pokemonname,Vanillaevomon.pokemonname),Targetmon.pokemonname).\
                                        order_by(func.coalesce(Vanillamon.pokemonname,Vanillaevomon.pokemonname),((func.sum(RandomizerEvolutionCounts.seedcount))/denominator).desc()).\
                                        all()
                dfdict[vanilla] = pd.DataFrame.from_records(evoquery,columns=['Base Pokemon','Vanilla Target','Randomizer Target','% Chance'])
                dfdict[vanilla]['% Chance'] = round(dfdict[vanilla]['% Chance'],2)
            return render_template('simple.html', tables=[df.to_html(classes='data', header="true",index=False) for df in dfdict.values()])
        else:
            evoquery = session.query(Basemon.pokemonname,func.coalesce(Vanillamon.pokemonname,Vanillaevomon.pokemonname),Targetmon.pokemonname,(func.sum(RandomizerEvolutionCounts.seedcount))/denominator).\
                                            select_from(RandomizerEvolutionCounts).\
                                            join(Targetmon,RandomizerEvolutionCounts.targetpokemonid == Targetmon.pokemonid).\
                                            join(Basemon,RandomizerEvolutionCounts.basepokemonid == Basemon.pokemonid).\
                                            join(Vanillamon,RandomizerEvolutionCounts.vanillatargetid == Vanillamon.pokemonid,isouter=True).\
                                            join(PokemonEvolutionInfo,(RandomizerEvolutionCounts.basepokemonid == PokemonEvolutionInfo.basepokemonid) & (RandomizerEvolutionCounts.vanillatargetid == None),isouter=True).\
                                            join(Vanillaevomon,PokemonEvolutionInfo.targetpokemonid == Vanillaevomon.pokemonid,isouter=True).\
                                            join(GameGroup,RandomizerEvolutionCounts.gamegroupid == GameGroup.gamegroupid).\
                                            filter((GameGroup.generationid == generation) & (Basemon.pokemonpokedexnumber == mondex)).\
                                            group_by(Basemon.pokemonname,func.coalesce(Vanillamon.pokemonname,Vanillaevomon.pokemonname),Targetmon.pokemonname).\
                                            order_by(func.coalesce(Vanillamon.pokemonname,Vanillaevomon.pokemonname),((func.sum(RandomizerEvolutionCounts.seedcount))/denominator).desc()).\
                                            all()
            df  = pd.DataFrame.from_records(evoquery,columns=['Base Pokemon','Vanilla Target','Randomizer Target','% Chance'])
            df['% Chance'] = round(df['% Chance'],2)
            #coalesce(vanillatargetid,(select targetpokemonid from pokemon.pokemonevolutioninfo evo where evo.basepokemonid = recf.basepokemonid))
            return render_template('simple.html',  tables=[df.to_html(classes='data', header="true",index=False)])
    except:
        traceback.print_exc()
        return "Error"

if __name__ == '__main__':
    app.run(host='127.0.0.1',port='5551')