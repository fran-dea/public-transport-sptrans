import networkx as nx
from geopy.distance import geodesic
from tqdm import tqdm

def cria_grafo(data, rotas, passageiros, viagens, paradas, estacoes_metro_e_trem):
    # Filtrar dados relevantes para a data
    rotas_data = rotas[rotas.data_referencia == data]
    passageiros_data = passageiros[passageiros.data == data]
    viagens_data = viagens[viagens.data_referencia == data]
    paradas_data = paradas[paradas.data_referencia == data]

    # Criar mapas para acesso rápido
    mapa_passageiros_data = dict(passageiros_data[['route_id', 'passageiros_total']].values)
    route_info = rotas_data.set_index('route_id')[['route_short_name', 'route_long_name', 'route_color', 'agency_id']].to_dict('index')

    G = nx.Graph()

    # Adicionar nós das paradas
    for _, row in paradas_data.iterrows():
        stop_id = row['stop_id']
        lat = row['stop_lat']
        lon = row['stop_lon']
        G.add_node(
            f"parada_{stop_id}",
            tipo='parada',
            latitude=lat,
            longitude=lon,
            bairro=row.get('NM_BAIRRO', None),
            populacao=row.get("v0001", None),
            subprefeituras=row.get("Subprefeituras ", None),
            regiao=row.get("Regiões", None),
            estacao_mais_proxima=row.get('nome_estacao_mais_proxima', None),
            dist_estacao_mais_proxima=row.get('dist_estacao_mais_proxima', None),
            nome_estacao_mais_proxima_existente=row.get('nome_estacao_mais_proxima_existente', None),
            dist_estacao_mais_proxima_existente=row.get('dist_estacao_mais_proxima_existente', None),
            nome_estacao_mais_proxima_projetado=row.get('nome_estacao_mais_proxima_projetado', None),
            dist_estacao_mais_proxima_projetado=row.get('dist_estacao_mais_proxima_projetado', None)
        )

    # Adicionar nós das estações
    for _, row in estacoes_metro_e_trem.iterrows():
        estacao_id = row['id']
        geometry = row['geometry']
        if isinstance(geometry, str) and geometry.startswith('POINT'):
            coords = geometry.replace('POINT (', '').replace(')', '').split()
            lon, lat = map(float, coords)
        else:
            continue

        G.add_node(
            f"estacao_{estacao_id}",
            tipo='estacao',
            existencia=row.get("existencia", None),
            latitude=lat,
            longitude=lon,
            nome=row['nm_estacao_metro_trem'],
            linha=row['nm_linha_metro_trem']
        )

    # Otimizar verificação de existência de arestas
    arestas_existentes = set()

    print("Adicionando arestas entre paradas...")
    for trip_id, grupo in tqdm(viagens_data.groupby('trip_id')):
        grupo_ordenado = grupo.sort_values(by='stop_sequence')
        stops = grupo_ordenado[['stop_id', 'stop_lat', 'stop_lon']].values
        route_id = grupo_ordenado['route_id'].iloc[0]
        passag = mapa_passageiros_data.get(route_id, None)
        info = route_info[route_id]
        route_short_name = info['route_short_name']
        route_long_name = info['route_long_name']
        route_color = info['route_color']
        agency_id = info['agency_id']

        for i in range(len(stops) - 1):
            id1 = f"parada_{int(stops[i][0])}"
            id2 = f"parada_{int(stops[i+1][0])}"
            edge_key = tuple(sorted((id1, id2)))

            if edge_key not in arestas_existentes:
                coord1 = (stops[i][1], stops[i][2])
                coord2 = (stops[i+1][1], stops[i+1][2])
                dist = geodesic(coord1, coord2).meters

                G.add_edge(
                    id1, id2,
                    peso_distancia=dist,
                    peso_passageiros=passag,
                    tipo='onibus',
                    route_id=route_id,
                    route_short_name=route_short_name,
                    route_long_name=route_long_name,
                    route_color=route_color,
                    agency_id=agency_id
                )
                arestas_existentes.add(edge_key)
            else:
                if passag is not None:
                    G[id1][id2]['peso_passageiros'] = passag

    print(f"{data} - Grafo final: {G.number_of_nodes()} nós e {G.number_of_edges()} arestas")
    return G
