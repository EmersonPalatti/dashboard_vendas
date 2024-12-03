import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# Ativando o ambiente virtual
# .\venv\Scripts/activate

# Rodando o aplicativo
# streamlit run Dashboard.py

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# Definindo o título do dashboard
st.title('DASHBOARD DE VENDAS :shopping_trolley:')

# Importando os dados
url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Nordeste', 'Sudeste', 'Sul', 'Norte', 'Centro-Oeste']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2022, 2023)

query_string = {'regiao': regiao.lower(), 'ano': ano}

response = requests.get(url, params=query_string) 
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Tabelas

### Tabelas de receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on='Local da compra', right_index=True).sort_values(by='Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))[['Preço']].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mês'] = receita_mensal['Data da Compra'].dt.month_name(locale='pt_BR')

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

### Tabelas de quantidade de vendas

qntd_vendas_estados = dados.groupby('Local da compra')[['Preço']].count()
qntd_vendas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(qntd_vendas_estados, left_on='Local da compra', right_index=True).sort_values(by='Preço', ascending=False)

vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))[['Preço']].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mês'] = vendas_mensal['Data da Compra'].dt.month_name(locale='pt_BR')

vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending=False))

### Tabelas vendedores

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg({'sum', 'count'}))

## Gráficos

### Gráficos de receita

fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat='lat',
                                  lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por estado')

fig_receita_mensal = px.line(receita_mensal,
                             x='Mês',
                             y='Preço',
                             markers=True,
                             range_y= (0, receita_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Receita Mensal'
                             )
fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_receita_estados = px.bar(receita_estados.head(5),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 Estados (receita)')
fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias,
                                text_auto = True,
                                title = 'Receita por Categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita')

### Gráficos de Quantidade de vendas

fig_mapa_vendas = px.scatter_geo(qntd_vendas_estados,
                                 lat='lat',
                                 lon='lon',
                                 scope='south america',
                                 size='Preço',
                                 template='seaborn',
                                 hover_name='Local da compra',
                                 hover_data={'lat': False, 'lon': False},
                                 title='Quantidade de vendas por estado')

fig_vendas_mensal = px.line(vendas_mensal,
                            x='Mês',
                            y='Preço',
                            markers=True,
                            range_y= (0, vendas_mensal.max()),
                            color = 'Ano',
                            line_dash = 'Ano',
                            title = 'Quantidade de vendas Mensal'
                            )
fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_estados = px.bar(qntd_vendas_estados.head(),
                            x = 'Local da compra',
                            y = 'Preço',
                            text_auto = True,
                            title = 'Top 5 Estados (quantidade de vendas)')
fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_categorias = px.bar(vendas_categorias,
                               text_auto = True,
                               title = 'Quantidade de vendas por Categoria')
fig_vendas_categorias.update_layout(yaxis_title='Quantidade de vendas')


## Visualização no Streamlit

aba1, aba2, aba3, aba4 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores', 'Base de dados'])

with aba1: 
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with col2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

with aba2: 
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_vendas_estados, use_container_width=True)
    with col2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} Vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores, use_container_width=True)                                
    with col2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} Vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores, use_container_width=True)

with aba4:
    st.dataframe(dados)        

# Mostrando a DF no dashboard
# st.dataframe(dados)

