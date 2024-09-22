import streamlit as st
from statsbombpy import sb
import matplotlib.pyplot as plt
from mplsoccer import Pitch,Sbopen
import pandas as pd
import time



parser = Sbopen()

st.set_page_config(layout='wide')
menu = ['CAMPEONATOS', "PARTIDAS"]
navegacao = st.sidebar.radio("Menu", menu)

@st.cache_data
def plot_pitches(df_pass):
    pitch = Pitch(pitch_color='#aabb97', line_color='white', stripe_color='#c2d59d', stripe=True)
    fig, ax = pitch.grid(grid_height=0.9, title_height=0.06, axis=False, endnote_height=0.04,
                         title_space=0, endnote_space=0)
    # Simulação da direção dos passes
    pitch.arrows(df_pass.x, df_pass.y, df_pass.end_x, df_pass.end_y, color='white', ax=ax['pitch'])
    # Mapa de calor
    pitch.kdeplot(x=df_pass.x, y=df_pass.y, ax=ax['pitch'], alpha=0.5, shade=True, cmap='plasma')
    return fig


def metricas_jogadores(eventos,jogador_escolhido):
    gols_marcados = eventos[(eventos['player']==jogador_escolhido) & (eventos["shot_outcome"]=='Goal')]['shot_outcome'].count()
    passes = eventos[(eventos['player']==jogador_escolhido) & (eventos["type"]=='Pass')]['type'].count()
    dribles= eventos[(eventos['player']==jogador_escolhido) & (eventos["type"]=='Dribble')]['type'].count()
    tempo_jogado = (int(eventos[eventos['player']==jogador_escolhido]['second'].astype(int).sum() / 60))
    return gols_marcados, passes, dribles, tempo_jogado


def download(eventos):
    csv = eventos.to_csv(index=False)
    
    if st.button("Download da partida"):
        with st.spinner("Preparando para baixar os dados..."):
            time.sleep(2)
            
        # Botão de download aparece após o clique
        st.download_button(label="Baixar os dados da partida",
                           data=csv,
                           file_name="Dados da partida.csv",
                           mime="text/csv")


def dashboard():
    if 'liga_escolhida' not in st.session_state:
        st.session_state.liga_escolhida = None
    if 'selecao_ano_temporada' not in st.session_state:
        st.session_state.selecao_ano_temporada = None
    
    ligas = sb.competitions()
    
    if navegacao == "CAMPEONATOS":
        st.subheader("CAMPEONATOS DISPONIVEIS")
        todas_ligas = ligas[["competition_name","country_name","season_name","competition_gender"]]
        st.write(todas_ligas)
    
    
    elif navegacao == 'PARTIDAS':
        st.subheader("Escolha um campeonato de sua preferência")
    
    # SELECIONANDO O CAMPEONATO    
        ligas_nomes = ligas["competition_name"].unique()        
        st.session_state.liga_escolhida = st.selectbox("LIGA DE FUTEBOL", ligas_nomes, 
            index=ligas_nomes.tolist().index(st.session_state.liga_escolhida) 
            if st.session_state.liga_escolhida in ligas_nomes.tolist() else 0)
        
        id_liga = ligas[ligas["competition_name"] == st.session_state.liga_escolhida]["competition_id"].values[0]
        
    # SELECIONANDO A TEMPORADA
        filtrando_temporada = ligas[ligas['competition_id'] == id_liga]
        ano_temporada = filtrando_temporada["season_name"].unique()
        st.session_state.selecao_ano_temporada = st.selectbox("ANO DA TEMPORADA", ano_temporada, 
            index=list(ano_temporada).index(st.session_state.selecao_ano_temporada) 
            if st.session_state.selecao_ano_temporada in ano_temporada else 0)
        id_temporada = filtrando_temporada[filtrando_temporada["season_name"] == st.session_state.selecao_ano_temporada]["season_id"].values[0]
        
    # SELECIONANDO AS PARTIDAS
        partidas = sb.matches(competition_id=id_liga, season_id=id_temporada)
    
    #'TODAS AS PARTIDAS'
        tab1, tab2 = st.tabs(['TODAS AS PARTIDAS','ANALISANDO UMA PARTIDA'])
        with tab1:
            partidas[['home_score','away_score']] = partidas[['home_score','away_score']].astype(str)
            partidas['Placar final'] = partidas['home_score'] + "  x  " + partidas['away_score']
            partidas['Partida Realizada'] = partidas['home_team'] + " x " + partidas['away_team']
            partidas_resultados = partidas[['match_date','stadium','competition_stage',
                                            'home_team','Placar final','away_team']]
            
            # Renomear colunas
            partidas_resultados = partidas_resultados.rename(columns={
                'match_date': 'Data da Partida',
                'stadium': 'Estádio',
                'home_team': 'Time da Casa',
                'away_team': 'Time Visitante'
            })
            
            st.subheader(f"Veja todas as partidas da Liga {st.session_state.liga_escolhida} na temporada {st.session_state.selecao_ano_temporada}")
            st.markdown(partidas_resultados.to_html(index=False), unsafe_allow_html=True)
    
    #'ANALISANDO UMA PARTIDA'
        with tab2:
            if 'partida_selecionada' not in st.session_state:
                st.session_state.partida_selecionada = None
            
            st.subheader(f"Veja a partida da Liga")
            partidas_realizadas = partidas['Partida Realizada'].unique()
            
            # AJUSTANDO O SESSION_STATE
            st.session_state.partida_selecionada = st.selectbox("Partida", partidas_realizadas, 
            index=list(partidas_realizadas).index(st.session_state.partida_selecionada) 
            if st.session_state.partida_selecionada in partidas_realizadas else 0)
            
            id_partida = partidas[partidas['Partida Realizada'] == st.session_state.partida_selecionada]['match_id'].values[0]
            
            col0,col1,col2 = st.columns([5,5,5])
            with col0:
                #Informações da partida
                st.write("Informações da Partida")
                etapa_do_jogo = partidas[partidas["match_id"]== id_partida]["competition_stage"].values[0]
                estadio = partidas[partidas["match_id"]== id_partida]["stadium"].values[0]
                arbitragem = partidas[partidas["match_id"]== id_partida]["referee"].values[0]
                st.markdown(f"<h5 style='font-size: 16px;'>⚽ Etapa</h5>", unsafe_allow_html=True)
                st.write(etapa_do_jogo)  # Exibe o valor da métrica
                
                st.markdown(f"<h5 style='font-size: 16px;'>🏟️ Estádio</h5>", unsafe_allow_html=True)
                st.write(estadio)
                
                st.markdown(f"<h5 style='font-size: 16px;'>Arbitro</h5>", unsafe_allow_html=True)
                st.write(arbitragem)
            
            # Dados da partida
            eventos = sb.events(match_id=id_partida)
            estatisticas = eventos[['team','type']].value_counts().reset_index(name='Estatisticas')
            

            with col1:
                #Time da Casa
                st.write("Time da Casa")
                time_casa = partidas.query("match_id == @id_partida")['home_team'].values[0]
                gols_time_casa = partidas.query("match_id == @id_partida")['home_score'].values[0]
                estatisticas_time_da_casa = estatisticas[estatisticas['team']== time_casa][['type','Estatisticas']]
                st.subheader(time_casa)
                st.metric("Gols",gols_time_casa)
                st.markdown(estatisticas_time_da_casa.to_html(index=False), unsafe_allow_html=True)
                
            with col2:    
                #Time visitante
                st.write("Time Visitante")
                time_visitante = partidas.query("match_id == @id_partida")['away_team'].values[0]
                gols_time_visitantes = partidas.query("match_id == @id_partida")['away_score'].values[0]
                estatisticas_time_visitante = estatisticas[estatisticas['team']== time_visitante][['type','Estatisticas']]
                st.subheader(time_visitante)
                st.metric("Gols",gols_time_visitantes)
                st.markdown(estatisticas_time_visitante.to_html(index=False), unsafe_allow_html=True)
        
        #ANALISANDO OS JOGADORES
            if 'jogador_escolhido_casa' not in st.session_state:
                st.session_state.jogador_escolhido_casa = None
            if 'jogador_escolhido_visit' not in st.session_state:
                st.session_state.jogador_escolhido_visit = None
                
            col3,col4 = st.columns(2)
            with col3:
                #Selecionar um jogador
                jogadores_da_partida = eventos[eventos['team']==time_casa]["player"].dropna().unique()
                st.session_state.jogador_escolhido_casa = st.selectbox("Escolha um jogador", jogadores_da_partida, 
            index=list(jogadores_da_partida).index(st.session_state.jogador_escolhido_casa) 
            if st.session_state.jogador_escolhido_casa in jogadores_da_partida else 0)

                gols_marcados, passes, dribles, tempo_jogado = metricas_jogadores(eventos,st.session_state.jogador_escolhido_casa)

                #metricas do jogador
                st.subheader(st.session_state.jogador_escolhido_casa)
                col5,col6,col7,col8 = st.columns(4)
                with col5:
                    st.metric('Gols Marcados', gols_marcados)
                with col6:
                    st.metric('Passes', passes)                
                with col7:
                    st.metric('Dribles', dribles)
                with col8:
                    st.metric('Munutos em Campo', tempo_jogado)                         
                
                #SESSION_STATE DAS ESTATISTICAS ESCOLHIDAS DOS JOGADORES
                if 'estatisticas_escolhidas' not in st.session_state:
                    st.session_state.estatisticas_escolhidas = []
                if 'estatisticas_escolhidas_visit' not in st.session_state:
                    st.session_state.estatisticas_escolhidas_visit = []

                #Selecionar estatisticas do jogador
                st.session_state.estatisticas_escolhidas = st.multiselect("Escolha as estatisticas para visualização",
                                                        eventos.type.unique(),
                                                        default=st.session_state.estatisticas_escolhidas,
                                                        key='estatisticas_casa')
                
                jogadores_selecao = eventos[(eventos['player'] == st.session_state.jogador_escolhido_casa) & 
                                            (eventos['type'].isin(st.session_state.estatisticas_escolhidas))]
                
                with st.expander('Mostrar todos os dados do jogador'):
                    st.write(jogadores_selecao)
                
                #PASSES EM CAMPO
                novo_evento = parser.event(id_partida)[0]
                filtro = novo_evento[(novo_evento['type_name'] == 'Pass') & (novo_evento['player_name'] == st.session_state.jogador_escolhido_casa)]
                df_pass = filtro.loc[:, ['x', 'y', 'end_x', 'end_y']]
                fig = plot_pitches(df_pass)
                st.pyplot(fig)
            with col4:
                #Selecionar um jogador
                jogadores_da_partida_visit = eventos[eventos['team']==time_visitante]["player"].dropna().unique()
                st.session_state.jogador_escolhido_visit = st.selectbox("Escolha um jogador", jogadores_da_partida_visit, 
            index=list(jogadores_da_partida_visit).index(st.session_state.jogador_escolhido_visit) 
            if st.session_state.jogador_escolhido_visit in jogadores_da_partida_visit else 0)

                gols_marcados, passes, dribles, tempo_jogado = metricas_jogadores(eventos,st.session_state.jogador_escolhido_visit)

                #metricas do jogador
                st.subheader(st.session_state.jogador_escolhido_visit)
                col9,col10,col11,col12 = st.columns(4)
                with col9:
                    st.metric('Gols Marcados', gols_marcados)
                with col10:
                    st.metric('Passes', passes)                
                with col11:
                    st.metric('Dribles', dribles)
                with col12:
                    st.metric('Munutos em Campo', tempo_jogado)  
                
                #Selecionar estatisticas do jogador
                st.session_state.estatisticas_escolhidas_visit = st.multiselect("Escolha as estatisticas para visualização",
                                                                eventos.type.unique(),
                                                                default=st.session_state.estatisticas_escolhidas_visit,
                                                                key='estatisticas_visitante')
                
                jogadores_selecao_visit = eventos[(eventos['player'] == st.session_state.jogador_escolhido_visit) & 
                                                  (eventos['type'].isin(st.session_state.estatisticas_escolhidas_visit))]
                
                with st.expander('Mostrar todos os dados do jogador'):
                    st.write(jogadores_selecao_visit)
                
                #PASSES EM CAMPO
                novo_evento = parser.event(id_partida)[0]
                filtro = novo_evento[(novo_evento['type_name'] == 'Pass') & (novo_evento['player_name'] == st.session_state.jogador_escolhido_visit)]
                df_pass = filtro.loc[:, ['x', 'y', 'end_x', 'end_y']]
                fig = plot_pitches(df_pass)
                st.pyplot(fig)
                
            

            #Dados completos da partida
            if st.checkbox("Ver todos os dados da Partida? "):
                st.write(eventos)
            
            download(eventos)
                    
            
            
# Executa o dashboard
if __name__ == "__main__":
    dashboard()